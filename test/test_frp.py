"""Tests for the Rizzo FRP fragment — the two later modalities and ⊛/5.

The typing rules are Rizzo fig. 3 (``spec/errata.md`` R1):

    delay : A → ⃝∀A                    ⊛ : ⃝∀(A→B) → ⃝∀A → ⃝∀B
    never : ⃝∃A                        5 : ⃝∀(A→B) → ⃝∃A → ⃝∃B
    wait  : Chan A → ⃝∃A               watch : Sig (Maybe A) → ⃝∃A
    sync  : ⃝∃A₁ → ⃝∃A₂ → ⃝∃(Sync A₁ A₂)
    head  : Sig A → A                  tail  : Sig A → ⃝∃(Sig A)
    (:::) : A → ⃝∃(Sig A) → Sig A      chan  : Chan A
    Γ, x : ⃝∀A ⊢ t : A  ⟹  Γ ⊢ gfix x. t : A

``⃝∀`` is written ``FaL`` and ``⃝∃`` is written ``ExL``; ``⊛`` is ``<*>``,
``5`` is ``<@>``, and ``▷`` is ``|>``.

The runtime tests re-enact §4.5's traces against ``reactive.py``: which
signals tick on which channel, and what values they hold afterwards.
"""

from __future__ import annotations

import pytest

from gestate.declarations import DeclError
from gestate.desugar import DesugarError
from gestate.gmachine import (GmError, NCon, NNum, NSig, SigHead, TAG_TAIL,
                              TAG_WATCH, run)
from gestate.pipeline import compile, evaluate
import gestate.reactive as _reactive
from gestate.reactive import (ReactiveError, _update_one, cl, init_program,
                              react, react_instant, ticked)
from gestate.unify import UnifyError


# ── Shared source fragments ──────────────────────────────────────────────────

# mkSig : ⃝∃A → ⃝∃(Sig A)
#   mkSig d = (λa. a :: mkSig d) ▷ d
# desugared per §2.4 into an explicit guarded fixed point (paper p. 27):
#   mkSig = fix r. λd. delay (λr'. λx. x :: r' d) ⊛ r 5 d
MKSIG = """
mkSig : ExL a -> ExL (Sig a)
mkSig = gfix r => (d => delay (r2 x => x ::: r2 d) <*> r <@> d)
"""

# map : (A → B) → Sig A → Sig B
#   map = fix r. λf. λs. f (head s) :: (delay (λr'. r' f) ⊛ r 5 tail s)
MAP = """
map : (a -> b) -> Sig a -> Sig b
map = gfix r => (f s => f (head s) ::: (delay (r2 => r2 f) <*> r <@> tail s))
"""


def _drive(source, inputs):
    """Compile, run, then feed ``(channel, value)`` inputs one at a time.

    Returns one snapshot per input: the ``(value, ticked)`` of every live
    signal, in now-heap order.
    """
    state = compile(source)
    reactive = init_program(state)
    snapshots = []
    for k, v in inputs:
        react(reactive, [(k, v)])
        snapshots.append([(_value(s), s.ticked) for s in state.now])
    return snapshots


def _value(sig: NSig):
    v = sig.value
    return v.n if isinstance(v, NNum) else v


# ── Typing ───────────────────────────────────────────────────────────────────


def test_delay_is_universal_and_a_tail_is_existential():
    """`delay t : ⃝∀A` is not a signal tail — `::` wants `⃝∃(Sig A)`.

    This is `spec/errata.md` R3: the guarded-recursion example the syntax
    spec used to give (`gfix self => 0 ::: delay self`) is ill-typed, and
    the reactive driver had a `ticked` case for `delay` purely to make it
    run.  There is no ⃝∀ → ⃝∃ coercion; `<@>` is the only bridge.
    """
    with pytest.raises(UnifyError, match=r"expected ExL[\s\S]*got FaL"):
        compile("main : Sig Int\nmain = gfix self => 0 ::: delay self\n")


def test_ap_ex_requires_a_universal_function():
    """`5 : ⃝∀(A→B) → ⃝∃A → ⃝∃B` — the function side may not be ⃝∃."""
    with pytest.raises(UnifyError, match=r"expected FaL[\s\S]*got ExL"):
        compile("c : Chan Int\nc = chan\n"
                "main : ExL Int\nmain = wait c <@> wait c\n")


def test_ap_fa_stays_universal():
    """`⊛` keeps both sides at ⃝∀, so its result is not a tail either."""
    with pytest.raises(UnifyError, match=r"expected ExL[\s\S]*got FaL"):
        compile("main : Sig Int\n"
                "main = 0 ::: (delay (x => x) <*> delay (1 ::: never))\n")


def test_signal_interface_typechecks():
    """head/tail/:::/never/wait/chan compose at the paper's types."""
    compile(
        MKSIG
        + "c : Chan Int\nc = chan\n"
        "xs : Sig Int\nxs = 0 ::: mkSig (wait c)\n"
        "nxt : ExL (Sig Int)\nnxt = tail xs\n"
        "now : Int\nnow = head xs\n"
        "still : Sig Int\nstill = 7 ::: never\n"
        "main : Int\nmain = head still\n"
    )


def test_the_two_later_modalities_are_writable_in_a_signature():
    """`fixme.md` F39: `FaL`/`ExL` exist as type constructors, so a program
    may *name* them.

    `ExL` is held hard — removed from `kindcheck._BUILTIN_KINDS`, 136 of
    780 language tests go red, because `signal.ges` writes `mkSig : ExL a
    -> ExL (Sig a)`.  `FaL` was held by nothing: removed on its own, 780
    stayed green, because inference constructs a `FaL` for every `delay`
    and no source in the tree ever writes one.  A written `FaL` is what
    this holds (batch 10, 2026-09-01).
    """
    compile("later : Int -> FaL Int\nlater n = delay (n + 1)\n\n"
            "main : Int\nmain = 1\n")


def test_maybe_and_sync_are_reserved():
    """`watch`/`sync` name these types, so a user copy would shadow them."""
    for name in ("Maybe", "Sync"):
        with pytest.raises(DeclError, match="built-in data type"):
            compile(f"{name} a := Foo | Bar a\nmain : Int\nmain = 1\n")


# ── head on a constant signal ────────────────────────────────────────────────


def test_head_of_cons():
    assert evaluate("main : Int\nmain = head (5 ::: never)\n") == "5"


# ── Runtime traces ───────────────────────────────────────────────────────────


def test_wait_driven_signal_updates_on_its_own_channel():
    """`l1 = 0 :: mkSig (wait κ1)` has clock {κ1} (paper fig. 4)."""
    source = (MKSIG
              + "c1 : Chan Int\nc1 = chan\n"
              "main : Sig Int\nmain = 0 ::: mkSig (wait c1)\n")
    snaps = _drive(source, [(0, 5), (0, 6)])

    assert snaps == [[(5, True)], [(6, True)]]


def test_map_computes_one_signal_from_another():
    """`map f xs` inherits xs's clock and applies f to each new value.

    Before ⊛/5 existed this was unreachable: `wait`-driven leaves were the
    only signals a program could build (`fixme.md` F14).
    """
    source = (MKSIG + MAP
              + "inc : Int -> Int\ninc n = n + 1\n"
              "c : Chan Int\nc = chan\n"
              "xs : Sig Int\nxs = 0 ::: mkSig (wait c)\n"
              "main : Sig Int\nmain = map inc xs\n")
    snaps = _drive(source, [(0, 5), (0, 6)])

    assert snaps[0] == [(5, True), (6, True)]     # xs = 5, map inc xs = 6
    assert snaps[1] == [(6, True), (7, True)]


def test_sample_depends_on_data_without_depending_on_timing():
    """`sample xs ys = map (\\x. (x, head ys)) xs` — paper fig. 4's `l6`.

    `cl (tail (sample xs ys)) = cl (tail xs)`, so the sampled signal
    updates only when `xs` does, while its *value* also reads `ys`.  That
    read goes through `head`, which is defined only on the now heap: `ys`
    is allocated before the sampler, so the sweep reaches it first.
    """
    source = (MKSIG + MAP
              + "c1 : Chan Int\nc1 = chan\n"
              "c2 : Chan Int\nc2 = chan\n"
              "xs : Sig Int\nxs = 0 ::: mkSig (wait c1)\n"
              "ys : Sig Int\nys = 100 ::: mkSig (wait c2)\n"
              "main : Sig Int\nmain = map (x => x + head ys) xs\n")
    snaps = _drive(source, [(0, 5), (1, 200), (0, 6)])

    # now-heap order is allocation order: xs, ys, main.
    assert snaps[0] == [(5, True), (100, False), (105, True)]
    # input on c2 updates ys but does *not* tick the sampler …
    assert snaps[1] == [(5, False), (200, True), (105, False)]
    # … and the next tick of xs picks up ys's new value.
    assert snaps[2] == [(6, True), (200, False), (206, True)]


def test_watch_fires_only_on_just():
    """`filter p s = mkSig (watch (mapMaybe p s))` — `spec/errata.md` R12.

    The partial signal must be updated before the signal watching it is
    consulted, and the watcher must *not* update on a step where the
    partial signal goes to `Nothing`.
    """
    source = (MKSIG + MAP
              + "small : Int -> Maybe Int\n"
              "small n = case n < 10 of\n"
              "    True -> Just n\n"
              "    False -> Nothing\n"
              "c : Chan Int\nc = chan\n"
              "xs : Sig Int\nxs = 0 ::: mkSig (wait c)\n"
              "ms : Sig (Maybe Int)\nms = map small xs\n"
              "main : Sig Int\nmain = 0 ::: mkSig (watch ms)\n")
    snaps = _drive(source, [(0, 3), (0, 50), (0, 7), (0, 99)])

    # (xs, ms, filtered) — only the filtered signal's ticks are asserted.
    assert [snap[2] for snap in snaps] == [
        (3, True),      # 3 < 10  → Just 3, watcher fires
        (3, False),     # 50      → Nothing, watcher holds 3
        (7, True),      # 7 < 10  → Just 7
        (7, False),     # 99      → Nothing, watcher holds 7
    ]


def test_sync_produces_a_matchable_sum():
    """`sync : ⃝∃A → ⃝∃B → ⃝∃(Sync A B)`, and `Sync` is ordinary data.

    `advance` used to hand back a delayed-computation node, so a `case`
    over it died with `no alt for tag 92` (`fixme.md` F16).
    """
    source = (MKSIG
              + "combine : Sync Int Int -> Int\n"
              "combine s = case s of\n"
              "    SyncLeft a -> a\n"
              "    SyncRight b -> b + 1000\n"
              "    SyncBoth a b -> a + b\n"
              "c1 : Chan Int\nc1 = chan\n"
              "c2 : Chan Int\nc2 = chan\n"
              "main : Sig Int\n"
              "main = 0 ::: mkSig (combine |> sync (wait c1) (wait c2))\n")
    snaps = _drive(source, [(0, 5), (1, 7), (0, 9)])

    assert [snap[0] for snap in snaps] == [(5, True), (1007, True), (9, True)]


# ── The channel context Δ ────────────────────────────────────────────────────


def test_channel_context_records_allocated_channels():
    """`⟨chan_A; σ/Δ⟩ ⇓ ⟨κ; σ/Δ, κ:Chan A⟩` — allocation extends Δ."""
    source = (MKSIG
              + "c : Chan Int\nc = chan\n"
              "main : Sig Int\nmain = 0 ::: mkSig (wait c)\n")
    reactive = init_program(compile(source))

    assert reactive.chans == {0: "Int"}


def test_unforced_channel_is_not_in_the_context():
    """A `chan` the program never evaluates was never allocated.

    Δ is a runtime context, not a list of declarations — laziness means a
    declared-but-unused channel does not exist.
    """
    source = (MKSIG
              + "c : Chan Int\nc = chan\n"
              "unused : Chan Int\nunused = chan\n"
              "main : Sig Int\nmain = 0 ::: mkSig (wait c)\n")
    reactive = init_program(compile(source))

    assert reactive.chans == {0: "Int"}


def test_input_on_an_unknown_channel_is_rejected():
    """`κ : Chan B ∈ Δ_n` is a premise of the productivity theorem."""
    source = (MKSIG
              + "c : Chan Int\nc = chan\n"
              "main : Sig Int\nmain = 0 ::: mkSig (wait c)\n")
    reactive = init_program(compile(source))

    with pytest.raises(ReactiveError, match="never allocated"):
        react(reactive, [(7, 1)])


def test_channel_element_type_is_recorded():
    source = (MKSIG + MAP
              + "small : Int -> Maybe Int\n"
              "small n = case n < 10 of\n"
              "    True -> Just n\n"
              "    False -> Nothing\n"
              "c : Chan Int\nc = chan\n"
              "xs : Sig Int\nxs = 0 ::: mkSig (wait c)\n"
              "ms : Sig (Maybe Int)\nms = map small xs\n"
              "main : Sig Int\nmain = 0 ::: mkSig (watch ms)\n")
    reactive = init_program(compile(source))

    assert reactive.chans == {0: "Int"}


# ── cl, and the ticked/cl invariant ──────────────────────────────────────────


def test_cl_of_a_wait_driven_signal_is_its_channel():
    source = (MKSIG
              + "c : Chan Int\nc = chan\n"
              "main : Sig Int\nmain = 0 ::: mkSig (wait c)\n")
    state = compile(source)
    init_program(state)
    sig = state.now[0]

    assert cl(sig.tail) == frozenset({("chan", 0)})


def test_cl_of_never_is_empty():
    state = compile("main : Sig Int\nmain = 7 ::: never\n")
    init_program(state)

    assert cl(state.now[0].tail) == frozenset()


def test_cl_of_sync_is_the_union():
    source = (MKSIG
              + "combine : Sync Int Int -> Int\n"
              "combine s = case s of\n"
              "    SyncLeft a -> a\n"
              "    SyncRight b -> b\n"
              "    SyncBoth a b -> a + b\n"
              "c1 : Chan Int\nc1 = chan\n"
              "c2 : Chan Int\nc2 = chan\n"
              "main : Sig Int\n"
              "main = 0 ::: mkSig (combine |> sync (wait c1) (wait c2))\n")
    state = compile(source)
    init_program(state)

    assert cl(state.now[0].tail) == frozenset({("chan", 0), ("chan", 1)})


def test_cl_of_a_sampler_is_the_sampled_signals_clock():
    """`cl (tail (sample xs ys)) = cl (tail xs)` — `ys` contributes nothing."""
    source = (MKSIG + MAP
              + "c1 : Chan Int\nc1 = chan\n"
              "c2 : Chan Int\nc2 = chan\n"
              "xs : Sig Int\nxs = 0 ::: mkSig (wait c1)\n"
              "ys : Sig Int\nys = 100 ::: mkSig (wait c2)\n"
              "main : Sig Int\nmain = map (x => x + head ys) xs\n")
    state = compile(source)
    init_program(state)
    xs, ys, sampler = state.now

    assert cl(xs.tail) == frozenset({("chan", 0)})
    assert cl(ys.tail) == frozenset({("chan", 1)})
    assert cl(sampler.tail) == cl(xs.tail)


def test_cl_of_a_watcher_names_the_partial_signal():
    source = (MKSIG + MAP
              + "small : Int -> Maybe Int\n"
              "small n = case n < 10 of\n"
              "    True -> Just n\n"
              "    False -> Nothing\n"
              "c : Chan Int\nc = chan\n"
              "xs : Sig Int\nxs = 0 ::: mkSig (wait c)\n"
              "ms : Sig (Maybe Int)\nms = map small xs\n"
              "main : Sig Int\nmain = 0 ::: mkSig (watch ms)\n")
    state = compile(source)
    init_program(state)
    _xs, ms, watcher = state.now

    assert cl(watcher.tail) == frozenset({("sig", ms)})


def test_ticked_cl_invariant_is_checked_every_step():
    """The driver compares `ticked` against the clock taken before the sweep.

    `check_clocks` is on by default; the traces above therefore all assert
    the fig. 10 invariant as a side effect.  This test makes the failure
    mode visible: a clock recomputed *after* the sweep started describes
    the next step, not this one.
    """
    source = (MKSIG
              + "c1 : Chan Int\nc1 = chan\n"
              "main : Sig Int\nmain = 0 ::: mkSig (wait c1)\n")
    state = compile(source)
    reactive = init_program(state)
    assert reactive.check_clocks

    react(reactive, [(0, 1)])
    sig = state.now[0]
    # A clock that does not mention channel 0 contradicts `ticked`.
    reactive.clocks = {sig: frozenset()}
    reactive.earlier = [sig]
    sig.current = False
    with pytest.raises(ReactiveError, match="ticked/cl disagree"):
        _update_one({0: NNum(2)}, reactive)


def test_the_sweep_snapshots_a_clock_for_every_signal_it_is_about_to_update(
        monkeypatch):
    """And the check above is only as good as the snapshot that feeds it.

    The test above sets `clocks` by hand and calls `_update_one` directly,
    so it holds the *comparison*.  Nothing held the *snapshot*: delete
    `reactive_step`'s `{sig: cl(sig.tail) …}` and `sig in reactive.clocks`
    is never true, the invariant silently stops being asked, and every
    test in this file — including the one above — still passes.  Measured
    2026-09-02 against 542 tests (`card:ungated-fixes.md`, batch 11);
    `fixme.md` F17.
    """
    source = (MKSIG
              + "c1 : Chan Int\nc1 = chan\n"
              "main : Sig Int\nmain = 0 ::: mkSig (wait c1)\n")
    state = compile(source)
    reactive = init_program(state)
    assert reactive.check_clocks

    sizes = []
    real = _reactive._update_one

    def spy(arrivals, r):
        sizes.append(len(r.clocks))
        return real(arrivals, r)

    monkeypatch.setattr(_reactive, "_update_one", spy)
    react_instant(reactive, [(0, 1)])

    assert sizes, "the sweep updated no signal at all"
    assert all(n > 0 for n in sizes), (
        f"the sweep ran with no clock snapshotted (sizes {sizes}): the "
        f"ticked/cl check above cannot fire, and nothing else notices")


# ── head is defined only on the now heap ─────────────────────────────────────


def test_head_of_an_earlier_heap_signal_is_stuck():
    """There is deliberately no rule for `head` on the earlier heap (§4.6.3).

    With one heap and in-place update the read would silently return last
    step's value, so the ✓ frontier is kept as a per-cell mark.
    """
    state = compile("main : Sig Int\nmain = 7 ::: never\n")
    init_program(state)
    sig = state.now[0]
    sig.current = False

    state.code = [SigHead()]
    state.stack = [sig]
    with pytest.raises(GmError, match="earlier heap"):
        run(state)


def test_the_frontier_is_restored_by_a_sweep():
    source = (MKSIG
              + "c : Chan Int\nc = chan\n"
              "main : Sig Int\nmain = 0 ::: mkSig (wait c)\n")
    state = compile(source)
    reactive = init_program(state)
    sig = state.now[0]
    assert sig.current

    react(reactive, [(0, 1)])
    assert sig.current            # back on the now heap after the sweep


# `head` is one of three readers of the ✓ frontier and the only one that
# was held.  `ticked` asks the same question of `watch l` and `tail l`
# through `_require_current`, whose fig. 10 rules are equally stated
# against the new heap — and deleting that check left all 542 tests green
# (`card:ungated-fixes.md`, batch 11, 2026-09-02).  `fixme.md` F18.


def test_watch_of_an_earlier_heap_signal_is_refused():
    state = compile("main : Sig Int\nmain = 7 ::: never\n")
    reactive = init_program(state)
    sig = state.now[0]
    sig.current = False
    with pytest.raises(ReactiveError, match="earlier heap"):
        ticked({}, NCon(TAG_WATCH, (sig,)), reactive)


def test_tail_of_an_earlier_heap_signal_is_refused():
    state = compile("main : Sig Int\nmain = 7 ::: never\n")
    reactive = init_program(state)
    sig = state.now[0]
    sig.current = False
    with pytest.raises(ReactiveError, match="earlier heap"):
        ticked({}, NCon(TAG_TAIL, (sig,)), reactive)


def test_an_error_in_the_sub_evaluation_does_not_wedge_the_machine(monkeypatch):
    """`advance` re-enters the evaluator on a *scratch* state (`_apply`).

    A `GmError` raised in user code run by the scheduler must not leave
    the live machine mid-frame, with code spliced in and a dump frame
    unbalanced.  The entry that repaired this read "dead code today
    (F14)" and F14 has been resolved since, so the branch is on the hot
    path — 61 of 281 reactive tests reach `_apply`, and none of them
    asked this.  `fixme.md` F20.

    **The reactive sweep is a separate question and is not atomic**: the
    same injected error empties `gm.now` and leaves it empty, silently.
    That is `fixme.md` F195, and this test deliberately does not claim it.
    """
    source = (MKSIG
              + "c1 : Chan Int\nc1 = chan\n"
              "main : Sig Int\nmain = 0 ::: mkSig (wait c1)\n")
    state = compile(source)
    reactive = init_program(state)
    react(reactive, [(0, 1)])
    before = (list(state.code), list(state.stack), list(state.dump))

    def boom(gm):
        raise GmError("injected failure inside the sub-evaluation")

    monkeypatch.setattr(_reactive, "run", boom)
    with pytest.raises(GmError, match="injected"):
        react(reactive, [(0, 2)])

    assert list(state.code) == before[0], "code left spliced by a failed re-entry"
    assert list(state.stack) == before[1], "stack left pushed by a failed re-entry"
    assert list(state.dump) == before[2], "dump frame left unbalanced"


# ── Surface syntax for guarded recursion (§2.4, errata R5) ───────────────────

# The same combinators as MKSIG/MAP above, written the way the paper
# writes them: recursive calls guarded by a `delay` (here supplied by the
# `|>` sugar), signal patterns instead of head/tail, and no `gfix` in
# sight.  The desugarer turns each into the explicit fixed point.
SURFACE = """
mkSig : ExL a -> ExL (Sig a)
mkSig d = (x => x ::: mkSig d) |> d

map : (a -> b) -> Sig a -> Sig b
map f (x ::: xs) = f x ::: (map f |> xs)
"""


def test_surface_guarded_recursion_runs():
    """`mkSig d = (\\a. a ::: mkSig d) |> d` and `map f (x ::: xs) = …`."""
    source = (SURFACE
              + "inc : Int -> Int\ninc n = n + 1\n"
              "c : Chan Int\nc = chan\n"
              "xs : Sig Int\nxs = 0 ::: mkSig (wait c)\n"
              "main : Sig Int\nmain = map inc xs\n")
    snaps = _drive(source, [(0, 5), (0, 6)])

    assert snaps[0] == [(5, True), (6, True)]
    assert snaps[1] == [(6, True), (7, True)]


def test_surface_and_explicit_fixed_point_agree():
    """The desugaring produces the paper's own core term.

    `map` written with `gfix`/`<*>`/`<@>` by hand and `map` written in
    surface syntax compile to the same supercombinators.
    """
    from gestate.declarations import classify
    from gestate.desugar import desugar_program, strip_annotations
    from gestate.syntax import parse

    def core(src, name):
        for n, arity, lam, _sig in desugar_program(classify(parse(src))):
            if n == name:
                return arity, repr(strip_annotations(lam))
        raise AssertionError(name)

    hand_arity, hand = core(MAP, "map")
    auto_arity, auto = core("map : (a -> b) -> Sig a -> Sig b\n"
                            "map f (x ::: xs) = f x ::: (map f |> xs)\n", "map")

    assert hand_arity == auto_arity == 0
    # Binder names differ (the desugarer mints its own); the shape does not.
    assert hand.count("EGFix") == auto.count("EGFix") == 1
    assert hand.count("EAppFa") == auto.count("EAppFa") == 1
    assert hand.count("EAppEx") == auto.count("EAppEx") == 1


def test_ordinary_recursion_is_left_alone():
    """No `delay` around the recursive call means no guarded fixed point."""
    assert evaluate("fact : Int -> Int\n"
                    "fact n = case n < 1 of\n"
                    "    True -> 1\n"
                    "    False -> n * fact (n - 1)\n"
                    "main : Int\nmain = fact 5\n") == "120"


def test_partly_guarded_recursion_is_rejected():
    """Rizzo requires *every* recursive call to be guarded."""
    source = (SURFACE
              + "bad : ExL Int -> Sig Int\n"
              "bad d = head (bad d) ::: ((x => x ::: bad d) |> d)\n"
              "main : Int\nmain = 0\n")
    with pytest.raises(DesugarError, match="every recursive call under a"):
        compile(source)


def test_signal_pattern_tail_must_be_a_variable():
    """The tail of `x ::: xs` is a delayed computation, not a signal.

    The *head* is an ordinary value and may be destructured (see
    ``test_signal_pattern_head_can_be_matched``); the tail sits at
    ``ExL (Sig A)`` and there is nothing there to match on.
    """
    with pytest.raises(DesugarError, match="only be bound to a variable"):
        compile("f : Sig Int -> Int\n"
                "f (x ::: (y ::: ys)) = x\n"
                "main : Int\nmain = 1\n")


def test_signal_pattern_head_can_be_matched():
    """`x ::: xs` is irrefutable, but its head is an ordinary value.

    Also `fixme.md` F44's own occasion: writing `f (Just x ::: xs)` in
    parameter position is what made the constructor branch's greedy
    sub-pattern visible, as a type error rather than a parse one.
    """
    assert evaluate("f : Sig (Maybe Int) -> Int\n"
                    "f (Just x ::: xs) = x\n"
                    "f (Nothing ::: xs) = 0\n"
                    "main : Int\nmain = f (Just 7 ::: never)\n") == "7"


def test_const_is_never_tailed():
    assert evaluate("const : a -> Sig a\nconst x = x ::: never\n"
                    "main : Int\nmain = head (const 42)\n") == "42"


def test_filter_in_surface_syntax():
    """`filter p s = mkSig (watch (nothing ::: mapMaybe p s))` (paper §2.2)."""
    source = (SURFACE
              + "small : Int -> Maybe Int\n"
              "small n = case n < 10 of\n"
              "    True -> Just n\n"
              "    False -> Nothing\n"
              "c : Chan Int\nc = chan\n"
              "xs : Sig Int\nxs = 0 ::: mkSig (wait c)\n"
              "ms : Sig (Maybe Int)\nms = map small xs\n"
              "main : Sig Int\nmain = 0 ::: mkSig (watch ms)\n")
    snaps = _drive(source, [(0, 3), (0, 50), (0, 7)])

    assert [snap[2] for snap in snaps] == [(3, True), (3, False), (7, True)]


def test_switch_with_a_local_cont():
    """The paper writes `cont` as a `where` clause; a lambda is the same.

    This needs a multi-line `case` inside brackets (`test_layout.py`) and
    a substitution that survives unifying the same two variables from
    both sides (`test_types.py`).
    """
    source = (SURFACE
              + "switch : Sig a -> ExL (Sig a) -> Sig a\n"
              "switch (x ::: xs) d = x ::: ((s => case s of\n"
              "    SyncLeft xs2 -> switch xs2 d\n"
              "    SyncRight d2 -> d2\n"
              "    SyncBoth d2 d3 -> d3) |> sync xs d)\n"
              "ca : Chan Int\nca = chan\n"
              "cb : Chan Int\ncb = chan\n"
              "la : Sig Int\nla = 0 ::: mkSig (wait ca)\n"
              "lb : Sig Int\nlb = 900 ::: mkSig (wait cb)\n"
              "main : Sig Int\nmain = switch la (tail lb)\n")
    state = compile(source)
    reactive = init_program(state)
    switched = state.stack[0]
    lb, la, _ = state.now
    chan_a = next(c for c in (0, 1) if ("chan", c) in cl(la.tail))
    chan_b = next(c for c in (0, 1) if ("chan", c) in cl(lb.tail))

    react(reactive, [(chan_a, 5)])
    assert _value(switched) == 5
    react(reactive, [(chan_b, 42)])
    assert _value(switched) == 42
    assert cl(switched.tail) == frozenset({("chan", chan_b)})


def test_switch_changes_its_clock():
    """`switch xs d` follows xs until d fires, then follows d (fig. 4's l5).

    The interesting part is the *clock*: before the switch the tail waits
    on both signals, afterwards only on the one it switched to.
    """
    source = (SURFACE
              + "cont : ExL (Sig a) -> Sync (Sig a) (Sig a) -> Sig a\n"
              "cont d s = case s of\n"
              "    SyncLeft xs2 -> switch xs2 d\n"
              "    SyncRight d2 -> d2\n"
              "    SyncBoth d2 d3 -> d3\n"
              "switch : Sig a -> ExL (Sig a) -> Sig a\n"
              "switch (x ::: xs) d = x ::: (cont d |> sync xs d)\n"
              "ca : Chan Int\nca = chan\n"
              "cb : Chan Int\ncb = chan\n"
              "la : Sig Int\nla = 0 ::: mkSig (wait ca)\n"
              "lb : Sig Int\nlb = 900 ::: mkSig (wait cb)\n"
              "main : Sig Int\nmain = switch la (tail lb)\n")
    state = compile(source)
    reactive = init_program(state)
    switched = state.stack[0]
    # `tail lb` is forced first, so lb — and hence `cb` — is allocated first.
    lb, la, _ = state.now
    chan_a = next(c for c in (0, 1) if ("chan", c) in cl(la.tail))
    chan_b = next(c for c in (0, 1) if ("chan", c) in cl(lb.tail))

    assert cl(switched.tail) == frozenset({("chan", chan_a), ("chan", chan_b)})

    react(reactive, [(chan_a, 5)])
    assert _value(switched) == 5            # still following la …
    assert cl(switched.tail) == frozenset({("chan", chan_a), ("chan", chan_b)})

    react(reactive, [(chan_b, 42)])
    assert _value(switched) == 42           # … switched to lb
    assert cl(switched.tail) == frozenset({("chan", chan_b)})

    react(reactive, [(chan_a, 6)])
    assert _value(switched) == 42           # la no longer drives it
    assert not switched.ticked


def test_signal_identity_survives_an_update():
    """`l` keeps its cell across steps — everything pointing at it sees
    the new value, and no duplicate signal is left on the now heap."""
    source = (MKSIG
              + "c : Chan Int\nc = chan\n"
              "main : Sig Int\nmain = 0 ::: mkSig (wait c)\n")
    state = compile(source)
    reactive = init_program(state)
    cell = state.now[0]

    for v in (1, 2, 3):
        react(reactive, [(0, v)])
        assert len(state.now) == 1
        assert state.now[0] is cell
        assert cell.value.n == v


# ── §4.5's `sample` trace, against heap shapes ───────────────────────────────
#
# `spec/syntax.md`'s testing strategy asks to "re-enact the sec 4.5 `sample`
# trace from `frp.md` against `reactive.py` and **assert per-step heap
# shapes**" (`fixme.md` F22).  The tests above assert per-step *values*,
# which is a weaker claim: a driver that reallocated a fresh cell on every
# update, or that let the live set grow, would produce identical values and
# pass all of them.  What §4.5 is actually about is the heap.

_SAMPLE = (MKSIG + MAP
           + "c1 : Chan Int\nc1 = chan\n"
           "c2 : Chan Int\nc2 = chan\n"
           "xs : Sig Int\nxs = 0 ::: mkSig (wait c1)\n"
           "ys : Sig Int\nys = 100 ::: mkSig (wait c2)\n"
           "main : Sig Int\nmain = map (x => x + head ys) xs\n")


def _sample_heap():
    """`init` plus the three live cells, in allocation order l1, l2, l3."""
    state = compile(_SAMPLE)
    reactive = init_program(state)
    return state, reactive, list(state.now)


def test_sample_allocates_three_signals_at_init():
    """§4.5: "allocates `l1, l2, l3` at init (three `SigCons`)"."""
    state, _reactive, cells = _sample_heap()
    assert len(cells) == 3
    assert all(isinstance(c, NSig) for c in cells)


def test_the_samplers_clock_is_the_sampled_signals():
    """The heap-level statement of what `sample` means.

    `l3`'s tail is `⃝∃`-applied over `tagTail [l1]`, so its clock is `l1`'s
    — it reads `l2`'s value but not `l2`'s timing.  Asserting the clock sets
    says that about the *node*, where a value test only says it about one
    trace.
    """
    _state, _reactive, (l1, l2, l3) = _sample_heap()
    assert cl(l1.tail) == frozenset({("chan", 0)})
    assert cl(l2.tail) == frozenset({("chan", 1)})
    assert cl(l3.tail) == cl(l1.tail)
    assert cl(l3.tail) != cl(l2.tail)


def test_updates_are_written_in_place():
    """§4.4's practical note: `hUpdate l …`, not a fresh cell pointing back.

    The identity of every cell survives every step, and the live set never
    grows.  A driver that allocated `l4` and repointed would pass every
    value test in this file and fail this one.
    """
    state, reactive, cells = _sample_heap()
    for chan, value in ((0, 5), (1, 200), (0, 6), (0, 7)):
        react(reactive, [(chan, value)])
        assert len(state.now) == 3, "the live set grew"
        assert all(a is b for a, b in zip(cells, state.now)), (
            "a signal was reallocated rather than updated in place")


def test_the_ticked_flags_follow_the_channel():
    """Which cells the sweep marks, per input — §4.5's trace line for line.

    On `κ1`: `l1` matches its `tagWait`, and `l3` ticks because `ticked`
    recurses into `tagTail [l1]` and `l1` was marked earlier in the *same*
    sweep, which is what the `l1 < l3` allocation ordering buys.  `l2` does
    not match `κ1` and is only re-filed with its flag cleared.
    """
    state, reactive, _cells = _sample_heap()

    react(reactive, [(0, 5)])
    assert [c.ticked for c in state.now] == [True, False, True]

    react(reactive, [(1, 200)])
    assert [c.ticked for c in state.now] == [False, True, False]

    react(reactive, [(0, 6)])
    assert [c.ticked for c in state.now] == [True, False, True]


def test_the_clocks_are_stable_across_steps():
    """A signal's clock is a property of its tail, not of the last sweep."""
    state, reactive, cells = _sample_heap()
    before = [cl(c.tail) for c in cells]
    for chan, value in ((0, 5), (1, 200), (0, 6)):
        react(reactive, [(chan, value)])
        assert [cl(c.tail) for c in state.now] == before


# ── The `filter` trace, against heap shapes (`errata.md` R12) ────────────────

_FILTER = (MKSIG + MAP
           + "small : Int -> Maybe Int\n"
           "small n = case n < 10 of\n"
           "    True -> Just n\n"
           "    False -> Nothing\n"
           "c : Chan Int\nc = chan\n"
           "xs : Sig Int\nxs = 0 ::: mkSig (wait c)\n"
           "ms : Sig (Maybe Int)\nms = map small xs\n"
           "main : Sig Int\nmain = 0 ::: mkSig (watch ms)\n")


def _filter_heap():
    state = compile(_FILTER)
    reactive = init_program(state)
    return state, reactive, list(state.now)


def test_a_watcher_has_a_signal_clock_not_a_channel_clock():
    """What makes `filter` structurally different from `sample`.

    `sample` inherits a *channel* clock through `tagTail`.  `watch l`'s
    clock is `{(sig, l)}` — whether it fires depends on the value `l` holds
    this instant, so `ticked` must read `l` after `l` has been updated in
    the same sweep.  That is the allocation-order invariant `frp.md` states
    for `tail l`, holding for `watch l` for the same reason.
    """
    _state, _reactive, (l1, l2, l3) = _filter_heap()
    assert cl(l1.tail) == frozenset({("chan", 0)})
    assert cl(l2.tail) == cl(l1.tail), "`map` inherits its source's clock"

    watched = cl(l3.tail)
    assert len(watched) == 1
    kind, target = next(iter(watched))
    assert kind == "sig"
    assert target is l2, "the watcher's clock names the signal it watches"


def test_the_watcher_holds_its_cell_through_a_nothing_step():
    """`l3` does not tick on `Nothing`, and is not reallocated either."""
    state, reactive, cells = _filter_heap()
    expected = [True, False, True, False]   # 3, 50, 7, 99
    for (value, fires) in zip((3, 50, 7, 99), expected):
        react(reactive, [(0, value)])
        assert len(state.now) == 3
        assert all(a is b for a, b in zip(cells, state.now))
        l1, l2, l3 = state.now
        assert l1.ticked and l2.ticked, "the source and the partial always tick"
        assert l3.ticked is fires, f"watcher on input {value}"


# ── An instant is a set of arrivals ──────────────────────────────────────────
#
# `fixme.md` F92, `spec/frp.md` §"Several arrivals in one instant".  The
# paper writes κ ↦ w — one channel per step — and `react` still means
# exactly that.  What `react_instant` adds is two clocks ticking *together*,
# which is what a block boundary is, and which `sync` was given `SyncBoth`
# for before there was an engine to want it.


TWO_CHANNELS = (SURFACE
                + "ca : Chan Int\nca = chan\n"
                "cb : Chan Int\ncb = chan\n"
                "la : Sig Int\nla = 0 ::: mkSig (wait ca)\n"
                "lb : Sig Int\nlb = 900 ::: mkSig (wait cb)\n")

#: `main` has to *reach* both signals or neither is ever allocated — a
#: top-level definition nothing forces is not evaluated, so the now heap
#: would be empty and there would be no clocks to read the channels off.
BOTH = ("main : Sig Int\n"
        "main = 0 ::: ((w => 1 ::: never) |> sync (tail la) (tail lb))\n")


def _two_channel_heap(main: str = BOTH):
    """Compile a two-channel program and name its channels by their clocks.

    Channel ids are handed out in *evaluation* order, so they are read back
    off the signals' clocks rather than assumed — the same trap `fixme.md`
    F91 was.
    """
    state = compile(TWO_CHANNELS + main)
    reactive = init_program(state)
    la = next(s for s in state.now if _value(s) == 0)
    lb = next(s for s in state.now if _value(s) == 900)
    chan_a = next(c for c in (0, 1) if ("chan", c) in cl(la.tail))
    chan_b = next(c for c in (0, 1) if ("chan", c) in cl(lb.tail))
    return state, reactive, chan_a, chan_b


def test_two_channels_in_one_instant_reach_sync_both():
    """`SyncBoth` from the driver, which was unreachable before.

    `_pack_both` fired only when both sides of a `sync` watched the *same*
    channel, so a `sync` across two clocks never produced it however the
    inputs were fed.  The alternatives are tagged so the value says which
    case ran: 1 for left only, 2 for right only, 3 for both.
    """
    which = ("which : Sync (Sig Int) (Sig Int) -> Int\n"
             "which s = case s of\n"
             "    SyncLeft x -> 1\n"
             "    SyncRight y -> 2\n"
             "    SyncBoth x y -> 3\n"
             "main : Sig Int\n"
             "main = 0 ::: ((w => which w ::: never) "
             "|> sync (tail la) (tail lb))\n")

    # A fresh heap per instant: `main`'s tail is `never` after it fires, so
    # one program cannot show both cases.
    s1, r1, a1, _b1 = _two_channel_heap(which)
    react_instant(r1, [(a1, 5)])
    assert _value(s1.stack[0]) == 1, "one channel: the left side alone"

    s2, r2, _a2, b2 = _two_channel_heap(which)
    react_instant(r2, [(b2, 42)])
    assert _value(s2.stack[0]) == 2, "the other channel: the right side"

    s3, r3, a3, b3 = _two_channel_heap(which)
    react_instant(r3, [(a3, 5), (b3, 42)])
    assert _value(s3.stack[0]) == 3, "both channels in one instant: SyncBoth"


def test_each_wait_reads_its_own_channels_value():
    """The half of the change with teeth.

    `advance` used to take one `input_node` and hand it down the recursion,
    so `wait κ` returned it whatever κ was — safe only because `ticked` had
    gated the call on a single channel.  With two arrivals that would give
    one side of a `sync` the other side's value, and nothing about the
    shape of the result would show it: both are `Int`.
    """
    state, reactive, chan_a, chan_b = _two_channel_heap()
    la = next(s for s in state.now if _value(s) == 0)
    lb = next(s for s in state.now if _value(s) == 900)

    react_instant(reactive, [(chan_a, 5), (chan_b, 42)])
    assert _value(la) == 5, "la waits on ca and must hold ca's value"
    assert _value(lb) == 42, "lb waits on cb and must hold cb's value"


def test_one_instant_is_not_two_instants():
    """Why the distinction is worth a change to the core.

    A signal downstream of *both* clocks advances **once** when they arrive
    together and **twice** when they arrive in sequence.  `counter` holds
    the number of times its own tail has fired, so the difference is a
    number rather than a description of one — which is the same defect
    `test_audiograph.py` measures as 8 against 48, one level down.
    """
    counter = ("tick : Int -> ExL (Sync (Sig Int) (Sig Int)) -> Sig Int\n"
               "tick n d = n ::: ((w => tick (n + 1) "
               "(sync (tail la) (tail lb))) |> d)\n"
               "main : Sig Int\n"
               "main = tick 0 (sync (tail la) (tail lb))\n")

    s1, r1, a1, b1 = _two_channel_heap(counter)
    react_instant(r1, [(a1, 5), (b1, 42)])
    assert _value(s1.stack[0]) == 1, "both clocks in one instant: one step"

    s2, r2, a2, b2 = _two_channel_heap(counter)
    react(r2, [(a2, 5), (b2, 42)])
    assert _value(s2.stack[0]) == 2, "the same two arrivals in sequence: two"


def test_a_channel_may_arrive_at_most_once_in_an_instant():
    """Two values on one channel is two instants, and saying so is the point.

    Letting the second silently win would drop an input; letting the first
    win would drop the newer one.  Neither is an instant.
    """
    _state, reactive, chan_a, _chan_b = _two_channel_heap()
    with pytest.raises(ReactiveError, match="two values in one instant"):
        react_instant(reactive, [(chan_a, 5), (chan_a, 6)])


def test_an_instant_with_no_arrivals_is_refused():
    """Nothing would be ticked, so the sweep would rewrite every signal
    unchanged — a step that is not a step."""
    _state, reactive, _a, _b = _two_channel_heap()
    with pytest.raises(ReactiveError, match="no arrivals"):
        react_instant(reactive, [])


def test_the_clock_check_still_holds_across_two_arrivals():
    """`ticked` and `cl` must agree per instant, not per channel.

    `check_clocks` is on by default and `_update_one` raises when the two
    disagree, so this passing at all is the assertion — but the clock is a
    *set of sources* and the arrivals are now a set too, and the invariant
    is that a signal fires when any of its sources is among them.
    """
    state, reactive, chan_a, chan_b = _two_channel_heap(
        "main : Sig Int\n"
        "main = 0 ::: ((w => 1 ::: never) |> sync (tail la) (tail lb))\n")
    assert reactive.check_clocks
    main = state.stack[0]
    assert cl(main.tail) == frozenset({("chan", chan_a), ("chan", chan_b)})

    react_instant(reactive, [(chan_a, 5), (chan_b, 42)])
    assert main.ticked


def test_react_is_still_one_arrival_one_instant():
    """The paper's rule, unchanged, and what every test above exercises."""
    _state, reactive, chan_a, _chan_b = _two_channel_heap()
    snapshots = react(reactive, [(chan_a, 5), (chan_a, 6), (chan_a, 7)])
    assert len(snapshots) == 3, "one snapshot per input, as `scanl` gives"
