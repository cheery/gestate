"""The static signal fragment — `spec/liveaudio.md` stage 1.

Two halves, and the second is the one that matters.

**It accepts a real synth.** Both committed examples are in the fragment,
which is what says the boundary is not drawn so tight that nothing useful
is inside it.

**It rejects the programs it is supposed to reject, by name.** A checker
that accepts everything passes no test, so every case below is a program
that *must* be refused, and each asserts which definition the message
blames. The list is `spec/liveaudio.md`'s own — a `List` in the state, a
function-typed step parameter, unbounded recursion — plus the ones writing
them turned up.

"A third clock" used to be on that list and is **not** any more: two
*rates* is the ceiling, and several control channels all tick at the same
one.  What replaced it is narrower and is in `test_audiograph.py` — a
control channel must carry a *scalar*, because a control value is one slot
of the buffer the host fills.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gestate.audiograph import check
from gestate.types import (TApp, TCon, TFun, TVar, is_flat, mk_tuple,
                           tuple_con, why_not_flat)

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"
EXAMPLES = ["blip.ges", "drums.ges"]


def _source(name: str) -> str:
    return (AUDIO_DIR / name).read_text()


# ── It accepts a real synth ─────────────────────────────────────────────────


@pytest.mark.parametrize("name", EXAMPLES)
def test_the_examples_are_in_the_fragment(name):
    """The half of the check that is easy to get wrong by being strict.

    Both examples needed the lookup-table rewrite to get here, and both
    render bit-identically to their stage-0 goldens after it — which is
    `test_audio.py`'s job and is why this one can be about the fragment.
    """
    report = check(_source(name))
    assert report, "\n".join(report.errors)


def test_the_classification_is_the_graph():
    """Not a by-product: stage 2 extracts its nodes from exactly these.

    `blip`'s signal chain is `ticks → scan → map → lowpass → gain`, and
    those are the definitions that carry a `Sig`.  Everything a step
    function calls is a scalar, and the one `chan` is the audio clock.
    """
    report = check(_source("blip.ges"))
    assert set(report.signals) == {"sound", "raw", "ticks", "gain", "lowpass"}
    assert report.clocks == ["clock"]
    # The tune, the oscillator, the envelope and the phase are step code.
    # `wrap` is `class Wrap`'s method now, so what the fragment sees is the
    # instance's generated name — resolved statically, which is exactly
    # what makes it admissible where a dictionary would not be.
    for name in ("noteOf", "noteAt", "envAt", "sawOf",
                 "__Wrap_Float_wrap__", "stepVoice"):
        assert name in report.scalars, name
    assert "__Functor_Sig_map__" not in report.scalars, \
        "a former is not a definition, whatever name it reached the graph under"


# ── It rejects what it must, and says which definition ──────────────────────
#
# Each case is `(program, definition-the-message-must-name, phrase)`.

REJECTED = {
    "a list read per sample": ("""
notes : List Float
notes = [1.0, 2.0]

nth : Int -> List Float -> Float
nth i xs = case xs of
    [] -> 0.0
    x :: rest -> case i == 0 of
        True -> x
        False -> nth (i - 1) rest

sound : Sig Float
sound = map (n => nth (prim_mod_int n 2) notes) ticks
""", "nth", "recursive"),

    "a list in the state": ("""
Hist := Hist Float (List Float)

stepHist : Hist -> Int -> Hist
stepHist h n = case h of
    Hist x xs -> Hist (toFloat n) (x :: xs)

outHist : Hist -> Float
outHist h = case h of
    Hist x xs -> x

sound : Sig Float
sound = map outHist (scan stepHist (Hist 0.0 []) ticks)
""", "stepHist", "List Float"),

    "a function-typed step parameter": ("""
apply : (Float -> Float) -> Float -> Float
apply f x = f x

double : Float -> Float
double x = x * 2.0

sound : Sig Float
sound = map (n => apply double (toFloat n)) ticks
""", "sound", "first-order"),

    "unbounded recursion": ("""
countdown : Int -> Float
countdown n = case n == 0 of
    True -> 0.0
    False -> countdown (n - 1) + 1.0

sound : Sig Float
sound = map countdown ticks
""", "countdown", "bounded"),

    # **The reason changed, and the change is the point.**  `elem` was
    # rejected for taking an `Eq Int` dictionary; `specialise.py` now gives
    # the call a copy with that dictionary substituted in, so the objection
    # left is the one `spec/liveaudio.md` said was the harder half all
    # along — it walks a cons list, per sample.  The definition named is
    # therefore the *copy*, which is why this matches on a prefix.
    "a polymorphic helper over a list": ("""
gateOf : Bool -> Float
gateOf b = case b of
    True -> 1.0
    False -> 0.0

sound : Sig Float
sound = map (n => gateOf (elem n [1, 2])) ticks
""", "elem#", "recursive and so has no fixed size"),

    "a set in a step function": ("""
setStep : Int -> Float
setStep n = case empty? {()} of
    True -> 0.0
    False -> toFloat n

sound : Sig Float
sound = map setStep ticks
""", "setStep", "set"),

    "a signal built by hand": ("""
sound : Sig Float
sound = 0.0 ::: never
""", "sound", "`:::`"),
}


@pytest.mark.parametrize("case", sorted(REJECTED))
def test_it_is_rejected_and_the_message_names_the_definition(case):
    source, definition, phrase = REJECTED[case]
    report = check(source)
    assert not report, f"{case} was accepted"

    # A `definition` ending in `#` names a *family*: `specialise.py` puts
    # the dictionaries it was given into the name, and which ones those are
    # is not what the case is about.
    named = [e for e in report.errors
             if e.startswith(definition if definition.endswith("#")
                             else f"{definition}:")]
    assert named, (f"no message names `{definition}`; got:\n"
                   + "\n".join(report.errors))
    assert any(phrase in e for e in named), (
        f"the message about `{definition}` does not say why "
        f"({phrase!r}):\n" + "\n".join(named))


def _bare(source: str, entry: str = "sound"):
    """Check a program without the audio prelude around it.

    The two cases below are about `sound` itself, and `audio.py` prepends
    `main = sound` — so as whole synth programs they would fail to *compile*
    rather than reach the fragment check at all.  `check_analysis` is the
    entry point for a tree you already have, and this is what it is for.
    """
    from gestate.audiograph import check_analysis
    from gestate.pipeline import analyse

    return check_analysis(analyse(source), entry=entry)


def test_the_entry_has_to_be_a_signal():
    report = _bare("sound : Float\nsound = 0.5\n")
    assert not report
    assert "must be a `Sig Float`" in report.message


def test_a_program_with_no_sound_says_so():
    report = _bare("main : Int\nmain = 1\n")
    assert not report
    assert "no `sound`" in report.message


def test_the_check_is_not_about_running_the_program():
    """`render()` runs programs the fragment rejects, and that is the point.

    The fragment is what the *engine* can compile, not what the language
    means — so the check has to be a separate question with a separate
    answer, or the offline renderer would have been narrowed to fit an
    engine that does not exist yet.
    """
    from gestate.audio import render

    source, _definition, _phrase = REJECTED["a list read per sample"]
    assert not check(source)
    samples = render(source, 8 / 400, 400)
    assert len(samples) == 8


# ── The flat types ──────────────────────────────────────────────────────────


def _cons() -> dict:
    from gestate.declarations import classify
    from gestate.prelude import merge
    return classify(merge("Pair := Pair Float Int\n"
                          "Deep := Deep (List Int)\n"
                          "main : Int\nmain = 1\n")).cons


def _t(name: str, *args):
    t = TCon(name)
    for a in args:
        t = TApp(t, a)
    return t


def test_what_is_flat():
    cons = _cons()
    for t in (TCon("Float"), TCon("Int"), TCon("Bool"), TCon("Char"),
              tuple_con(0), _t("Pair"),
              mk_tuple([TCon("Float"), TCon("Int")]),
              _t("Maybe", TCon("Float"))):
        assert is_flat(t, cons), t


def test_what_is_not_flat_and_why():
    """The message has to say which part, or it is not worth printing."""
    cons = _cons()
    cases = [
        (_t("List", TCon("Float")), "recursive"),
        (_t("Set", TCon("Int")), "unbounded size"),
        (_t("Sig", TCon("Float")), "a signal"),
        (TFun(TCon("Int"), TCon("Int")), "a function"),
        (TVar(1), "type variable"),
        (_t("Deep"), "field List Int"),
    ]
    for t, phrase in cases:
        assert not is_flat(t, cons), t
        assert phrase in why_not_flat(t, cons), (t, why_not_flat(t, cons))


def test_an_unknown_type_is_a_rejection_here_and_not_elsewhere():
    """The one place this grammar is *stricter* than Datafun's four.

    `is_eqtype` answers "allowed" for a variable, because refusing would
    make every polymorphic set function unwritable.  A variable is exactly
    what cannot be laid out in a state struct, so here it is a refusal —
    and that is what makes the fragment monomorphic without a second rule.
    """
    from gestate.types import is_eqtype, is_fixtype

    assert is_eqtype(TVar(1)) and is_fixtype(TVar(1))
    assert not is_flat(TVar(1))


# ── The CLI ─────────────────────────────────────────────────────────────────


def test_the_cli_accepts_an_example(capsys):
    from gestate.audiograph import main

    assert main([str(AUDIO_DIR / "drums.ges")]) == 0
    assert "in the fragment" in capsys.readouterr().out


def test_the_cli_reports_a_program_that_is_not(tmp_path, capsys):
    from gestate.audiograph import main

    bad = tmp_path / "bad.ges"
    bad.write_text(REJECTED["unbounded recursion"][0])
    assert main([str(bad)]) == 1
    out = capsys.readouterr().out
    assert "not in the static signal fragment" in out
    assert "countdown" in out


# ── A constructor's own parameters are not the question ─────────────────────


def test_a_parametric_payload_is_in_the_fragment():
    """`fixme.md` F96.

    The check reads a constructor's *declared* result type, so `Played a`
    was refused for having an `a` in it — while `is_flat` says `Played
    Custom` is flat and the extractor substitutes and lays it out.  It was
    rejecting a whole class of program the fragment admits, which is the
    one thing a fragment check must not do.
    """
    from gestate.audioextract import extract

    source = """
Played a := Played Int Int a
Custom := Custom Float Int

c : Chan Int
c = chan

s : Sig Int
s = 0 ::: mkSig (wait c)

mk : Int -> Int -> Played Custom
mk n k = Played n 0 (Custom 1.5 k)

useIt : Custom -> Float
useIt cc = case cc of
    Custom f i -> f * toFloat i * 0.001

out : Played Custom -> Float
out p = case p of
    Played on off cc -> useIt cc

sound : Sig Float
sound = map out (zip mk ticks s)
"""
    report = check(source, rate=1000)
    assert bool(report), report.message

    # And the extractor agrees, which is the property that matters: the
    # check must promise only what the next stage delivers.
    graph = extract(source, rate=1000)
    assert graph.layouts["Played Custom"][0]["fields"] == \
        ["Int", "Int", "Custom"]


def test_a_list_is_still_refused_and_says_why():
    """The loosening must not let recursion through.

    `List` is recursive whatever its element is, so substituting a
    stand-in for the parameter cannot make it flat — which is exactly why
    judging the *shape* is safe.
    """
    source = """
sumOf : List Int -> Int
sumOf xs = case xs of
    [] -> 0
    y :: ys -> y + sumOf ys

step : Int -> Float
step n = toFloat (sumOf [n, n])

sound : Sig Float
sound = map step ticks
"""
    report = check(source, rate=1000)
    assert not report
    assert "recursive" in report.message


# ── A signal definition may be polymorphic ──────────────────────────────────
#
# Because it is *inlined* at every use, at that use's own type — so its type
# variables are gone before anything is built.  A step function is not
# inlined, survives into the IR as a function, and a function of unknown
# size has nothing to be generated as.  Judging both by the declared type
# was `fixme.md` F96's mistake in a second place.


POLY_SIGNAL = """level : Sig Float
level = mkKnob 0.6

pitch : Sig Int
pitch = mkKnob 40

Reading := Reading Int Float

readAt : Int -> Float -> Reading
readAt p l = Reading p l

outAt : Reading -> Float
outAt r = case r of
    Reading p l -> sineOf (wrap (toFloat p * 0.001)) * l

sound : Sig Float
sound = map outAt (zip readAt pitch level)
"""


def test_one_polymorphic_helper_serves_two_element_types():
    """`mkKnob : a -> Sig a`, used at `Float` and at `Int` in one program."""
    from gestate.audioextract import extract

    graph = extract(POLY_SIGNAL, rate=8000)
    sources = {n.type_: n.init for n in graph.control_sources()}
    assert sources == {"Float": 0.6, "Int": 40}


def test_a_polymorphic_signal_definition_is_in_the_fragment():
    from gestate.audiograph import check

    assert check(POLY_SIGNAL, rate=8000).errors == []


def test_no_type_variable_survives_into_the_graph():
    """The allowance is real only because nothing polymorphic is left.

    A node typed `a` would reach `audiollvm.Types.of` and have no layout,
    which is the disagreement between checker and extractor that `fixme.md`
    F95 is about.
    """
    from gestate.audioextract import extract

    graph = extract(POLY_SIGNAL, rate=8000)
    for node in graph.nodes:
        assert node.type_ in graph.layouts or node.type_ in ("Int", "Float"), \
            f"node {node.id} is typed `{node.type_}`, which has no layout"


def test_a_polymorphic_step_function_is_still_refused():
    """The other half of the rule, and the reason it is a rule.

    A step survives into the IR as a function; `audiollvm` emits it once,
    at the one type it has.  A type variable there has no size and nothing
    downstream could recover it.
    """
    from gestate.audiograph import check

    report = check(
        "twice : a -> a\ntwice x = x\n"
        "\nsound : Sig Float\nsound = map (n => twice 0.5) ticks\n",
        rate=8000)
    assert any("monomorphic" in e for e in report.errors), report.errors


def test_a_polymorphic_signal_parameter_is_in_the_fragment():
    """It used to be refused, and the reason did not survive contact.

    "A definition does not know the element type of a signal it was
    handed" is true of the definition and false of the program: the
    argument is itself a definition with a type of its own, and inlining
    is what brings the two together.  Keeping the line here is what stopped
    the prelude from holding anything that works on a note — see
    `adsr`, which every polyphonic example used to write out against
    its own payload type (`spec/frp_lesson.md`).
    """
    from gestate.audiograph import check

    assert check(
        "hold : Sig a -> Sig a\nhold s = s\n"
        "\nsound : Sig Float\nsound = hold (map (n => 0.5) ticks)\n",
        rate=8000).errors == []


def test_a_polymorphic_parameter_settles_before_the_graph():
    """The allowance is real only because nothing polymorphic is left.

    `heldOf : Sig (Both Gate a) -> Sig a` is the shape that motivated it:
    its signature has no layout and never will, and the argument's own
    construction is what says `Both Gate Key`.
    """
    from gestate.audioextract import extract

    graph = extract(
        "Key := Key Int Int\n"
        "\nheldOf : Sig (Both Gate a) -> Sig a\n"
        "heldOf s = map (n => case n of\n"
        "    Both w q -> q) s\n"
        "\nnotes : Sig (Both Gate Key)\n"
        "notes = map (n => Both (Gate 1 0) (Key 60 100)) ticks\n"
        "\nkeyOf : Key -> Float\n"
        "keyOf q = case q of\n"
        "    Key k v -> keyHz k\n"
        "\nsound : Sig Float\n"
        "sound = sine (!keyOf (heldOf notes))\n",
        rate=8000)
    for node in graph.nodes:
        assert node.type_ in graph.layouts or node.type_ in ("Int", "Float"), \
            f"node {node.id} is typed `{node.type_}`, which has no layout"


def test_a_function_typed_parameter_is_still_refused():
    """Where the line moved *to*.

    A parameter may be polymorphic; it may not be a function.  A
    combinator that took the projection to apply — `onNote f s` — is a
    closure by another name, and the fragment admits none, which is why
    the lift is `!f s` at the call site instead.
    """
    from gestate.audiograph import check

    report = check(
        "twiceOver : (Float -> Float) -> Sig Float -> Sig Float\n"
        "twiceOver f s = map (x => f (f x)) s\n"
        "\ndouble : Float -> Float\ndouble x = x * 2.0\n"
        "\nsound : Sig Float\n"
        "sound = twiceOver double (map (n => 0.25) ticks)\n",
        rate=8000)
    assert not report, "a function parameter was accepted"
    assert any("function" in e for e in report.errors), report.errors


# ── A class instance at `Sig` — Fran's lift ─────────────────────────────────
#
# `spec/frp_lesson.md`: in Fran an expression over behaviours *is* the
# program — `woo = stretch (abs wiggle) charlotte` — and the reason gestate
# read as ceremony beside it was that arithmetic on signals had to be
# spelled `zip (x y => x * y) a b`.  It need not: the instance below is
# ordinary code, and every pass but one already handled it.  The one was
# this checker, which judged a method by the *name* of its instance head.
#
# What it now judges instead is the method's type, which `elaborate` states
# whenever the instance is monomorphic and takes no dictionary.

#: `Num (Sig Float)` and `Floating (Sig Float)` are `audio.ges`'s, so this
#: is the lift as it *ships* rather than a copy written for the test — and
#: the literals are bare, which is what `Floating` bought: `0.5` means a
#: constant signal here because the program's instance says so.
LIFTED = """wiggle : Sig Float
wiggle = sine 3.0

sound : Sig Float
sound = sine 440.0 * (0.5 + wiggle * 0.25)
"""

#: The same signal, with every lift written out.  What `LIFTED` has to mean.
UNLIFTED = """wiggle : Sig Float
wiggle = sine 3.0

depth : Sig Float
depth = zip (x y => x * y) wiggle (constSig 0.25)

amount : Sig Float
amount = zip (x y => x + y) (constSig 0.5) depth

sound : Sig Float
sound = zip (x y => x * y) (sine 440.0) amount
"""


def test_arithmetic_on_signals_is_in_the_fragment():
    """`tone * env`, where both are signals."""
    from gestate.audiograph import check

    assert check(LIFTED, rate=8000).errors == []


def test_a_lifted_program_is_the_unlifted_one():
    """Sample for sample — the lift is spelling, not meaning.

    The strongest statement available: if `*` at `Sig Float` produced
    anything but the `zip` its instance says it is, these would differ.
    """
    from gestate.audioengine import run
    from gestate.audioextract import extract

    lifted = run(extract(LIFTED, rate=8000), 400)
    assert lifted == run(extract(UNLIFTED, rate=8000), 400)
    assert any(x != 0.0 for x in lifted), "silent: nothing was compared"


def test_a_lifted_program_reaches_the_engine():
    """Not only the interpreter — the generated code agrees, bit for bit.

    This is the half that was refused: the oracle always ran this program,
    and the engine could not be given a graph for it.
    """
    import shutil
    import tempfile

    if shutil.which("clang") is None:
        pytest.skip("no clang to build the engine with")

    from gestate.audioengine import run
    from gestate.audioextract import extract
    from gestate.audiollvm import run_native

    graph = extract(LIFTED, rate=8000)
    with tempfile.TemporaryDirectory() as directory:
        assert run_native(graph, directory, 256, block=64) == \
            run(graph, 256, block=64)


def test_a_method_that_takes_a_dictionary_is_still_refused():
    """The rule that replaced the head whitelist, at its own boundary.

    `Eq (List a)` has a type variable in its head, so no substitution makes
    the method monomorphic and `elaborate` states no type for it.  The
    fragment cannot lay out a dictionary, so this stays refused — and now
    says which of the two it is.
    """
    from gestate.audiograph import check

    report = check(
        "sound : Sig Float\n"
        "sound = map (n => case [n] == [1] of\n"
        "    True -> 1.0\n"
        "    False -> 0.0) ticks\n",
        rate=8000)
    assert not report, "a dictionary reached the fragment"
    assert any("polymorphic" in e or "dictionary" in e
               for e in report.errors), report.errors


# ── A former inside a former, with a lambda step ────────────────────────────


def test_a_nested_former_with_a_lambda_step_is_typed():
    """It could not be, and the reason was that nobody kept the type.

    A former is typed by its step — `zip f l r` with `f : a -> b -> c`
    means `l : Sig a` — and a lambda step's arrow was inferred and then
    dropped, so a former nested directly inside another had nothing to be
    typed from.  The workaround was to give the inner signal a name whose
    only job was to carry a type, which is plumbing in code about a sound
    (`spec/frp_lesson.md`).  `ELambda.type_` is where inference now keeps
    it.
    """
    from gestate.audioengine import run
    from gestate.audioextract import extract

    nested = extract(
        "wiggle : Sig Float\nwiggle = sine 3.0\n"
        "\nsound : Sig Float\n"
        "sound = zip (x y => x * y) (map (n => 0.25) ticks) wiggle\n",
        rate=8000)
    named = extract(
        "wiggle : Sig Float\nwiggle = sine 3.0\n"
        "\nquarter : Sig Float\nquarter = map (n => 0.25) ticks\n"
        "\nsound : Sig Float\n"
        "sound = zip (x y => x * y) quarter wiggle\n",
        rate=8000)
    assert run(nested, 200) == run(named, 200)
    assert any(x != 0.0 for x in run(nested, 200)), "silent"


# ── `!` — an application lifted over signals ────────────────────────────────
#
# One marker, as many arguments as the function takes.  Written rather than
# inferred: a lift a compiler inserted where types disagreed would put a
# node in the graph the author never wrote, and stage 5 migrates running
# state by comparing node *origins*.


def _run(source: str, samples: int = 300, rate: int = 8000) -> list:
    from gestate.audioengine import run
    from gestate.audioextract import extract

    return run(extract(source, rate=rate), samples)


def test_a_lift_with_no_arguments_is_a_constant_signal():
    """`!x` is applicative `pure`."""
    assert _run("sound : Sig Float\nsound = !0.25\n", 4) == [0.25] * 4
    assert _run("sound : Sig Float\nsound = !0.25\n", 4) == \
        _run("sound : Sig Float\nsound = constSig 0.25\n", 4)


def test_a_lift_over_one_signal_is_a_map():
    source = ("hzOf : Int -> Float\nhzOf k = keyHz k\n"
              "\npitch : Sig Int\npitch = constSig 60\n"
              "\nsound : Sig Float\nsound = {}\n")
    assert _run(source.format("sine (!hzOf pitch)")) == \
        _run(source.format("sine (map hzOf pitch)"))


def test_a_lift_over_two_signals_is_a_zip():
    source = ("blend : Float -> Float -> Float\n"
              "blend a b = a * 0.5 + b * 0.5\n"
              "\nsound : Sig Float\nsound = {}\n")
    got = _run(source.format("!blend (sine 440.0) (sine 660.0)"))
    assert got == _run(source.format(
        "zip blend (sine 440.0) (sine 660.0)"))
    assert any(x != 0.0 for x in got), "silent"


def test_a_lift_over_three_signals_pairs_them_up():
    """There is no three-signal former, so `Both` carries the extra one.

    Compared against writing that out by hand, which is what the `voices`
    expander does with its own `Part` records for the same reason.
    """
    base = ("mix3 : Float -> Float -> Float -> Float\n"
            "mix3 a b c = a * 0.5 + b * 0.3 + c * 0.2\n")
    lifted = base + ("\nsound : Sig Float\n"
                     "sound = !mix3 (sine 100.0) (sine 200.0) "
                     "(sine 300.0)\n")
    by_hand = base + ("\nPair := Pair Float Float\n"
                      "\npaired : Sig Pair\n"
                      "paired = zip (a b => Pair a b) (sine 100.0) "
                      "(sine 200.0)\n"
                      "\napply3 : Pair -> Float -> Float\n"
                      "apply3 p c = case p of\n"
                      "    Pair a b -> mix3 a b c\n"
                      "\nsound : Sig Float\n"
                      "sound = zip apply3 paired (sine 300.0)\n")
    got = _run(lifted)
    assert got == _run(by_hand)
    assert any(x != 0.0 for x in got), "silent"


def test_the_marker_may_take_the_parenthesised_application():
    """`!(f x y)` and `!f x y` are the same lift."""
    source = ("blend : Float -> Float -> Float\n"
              "blend a b = a * 0.5 + b * 0.5\n"
              "\nsound : Sig Float\nsound = {}\n")
    assert _run(source.format("!(blend (sine 440.0) (sine 660.0))")) == \
        _run(source.format("!blend (sine 440.0) (sine 660.0)"))


def test_a_signal_of_functions_is_refused():
    """Why `!` is one marker over an application rather than a chain.

    Haskell's `f <$> x <*> y` builds the partially applied `Sig (b -> c)`
    between the two lifts, and a signal of functions has no layout in a
    state struct — so the notation could only ever have been fused, and a
    marker that takes the whole application says so up front.
    """
    report = check(
        "partial : Sig (Float -> Float)\n"
        "partial = map (n => (y => toFloat n + y)) ticks\n"
        "\nsound : Sig Float\nsound = map (f => f 1.0) partial\n",
        rate=8000)
    assert not report
    assert any("function" in e for e in report.errors), report.errors
