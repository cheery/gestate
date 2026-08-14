"""What `pipeline.analyse` may hand out twice — `fixme.md` F99.

The front end is the expensive half of everything here, and one text is
run through it several times a second by readers that know nothing of each
other: the engine's graph, the knob placement, the `FromMIDI` instances,
the sidebar, `?` and `Tab`.  So the answer is kept.

Keeping it is only sound because an `Analysis` is a pure function of its
source *and stays usable* — a later front end must not disturb one, and
`compile` must read rather than rewrite it.  Inference is destructive
through a module global (`types.unifying`), which is exactly the kind of
thing that would make the second claim false, so both are tested here
rather than assumed.  If either of these fails, the cache in
`pipeline.analyse` is not safe and the speed it buys is not worth having.
"""

from __future__ import annotations

from gestate.audio import assemble
from gestate.audioengine import run as run_graph
from gestate.audioextract import extract_analysis
from gestate.pipeline import (analyse, compile as pcompile, forget_analyses,
                              _KEEP_ANALYSED, _analysed)
from gestate.show import show_type

RATE = 8000

SYNTH = """cutoff : Sig Float
cutoff = mkKnob 0.6

sound : Sig Float
sound = zip (x c => x * c) (sine 220.0) cutoff
"""


def _types(analysis) -> list:
    return sorted((str(n), show_type(t)) for n, t in analysis.types.items())


def _graph(analysis):
    return extract_analysis(analysis, entry="sound", rate=RATE)


def test_the_same_text_is_analysed_once():
    forget_analyses()
    src = assemble(SYNTH, RATE)
    assert analyse(src) is analyse(src)


def test_a_different_text_is_a_different_answer():
    forget_analyses()
    a = analyse(assemble(SYNTH, RATE))
    b = analyse(assemble(SYNTH.replace("220.0", "330.0"), RATE))
    assert a is not b
    assert _graph(a).nodes != _graph(b).nodes or True   # both extract at all
    assert run_graph(_graph(a), 64) != run_graph(_graph(b), 64)


def test_an_analysis_survives_another_front_end():
    """Inference is destructive through a *module global*, so this is the
    claim most likely to be false — and the one the cache rests on."""
    forget_analyses()
    src = assemble(SYNTH, RATE)
    kept = analyse(src)
    types, samples = _types(kept), run_graph(_graph(kept), 128)

    analyse("main : Int\nmain = 1 + 2\n")      # someone else's program
    analyse(assemble(SYNTH.replace("220.0", "440.0"), RATE))

    assert _types(kept) == types
    assert run_graph(_graph(kept), 128) == samples


def test_compiling_does_not_rewrite_the_analysis_it_read():
    """`compile` continues from `analysis.scs` through lifting and the ϕ/δ
    transform, and now does it to an object someone else is holding."""
    forget_analyses()
    src = assemble(SYNTH, RATE)
    kept = analyse(src)
    scs, types, samples = len(kept.scs), _types(kept), run_graph(_graph(kept), 128)

    pcompile(src)                              # the same text, all the way

    assert len(kept.scs) == scs
    assert _types(kept) == types
    assert run_graph(_graph(kept), 128) == samples


def test_a_datafun_program_survives_its_own_transform():
    """The hardest case: ϕ/δ rewrites a program with sets in it."""
    forget_analyses()
    src = "main : Set Int\nmain = {1, 2} \\/ {3}\n"
    kept = analyse(src)
    scs, types = len(kept.scs), _types(kept)
    pcompile(src)
    assert (len(kept.scs), _types(kept)) == (scs, types)


def test_only_a_few_are_kept():
    """An editor has three assemblies of one file live at once and a fourth
    slot for what survives a keystroke — not a session's worth of memory."""
    forget_analyses()
    for i in range(_KEEP_ANALYSED + 3):
        analyse(f"main : Int\nmain = {i}\n")
    assert len(_analysed) == _KEEP_ANALYSED


def test_forgetting_is_what_a_measurement_needs():
    forget_analyses()
    src = assemble(SYNTH, RATE)
    first = analyse(src)
    forget_analyses()
    assert analyse(src) is not first, "otherwise nothing can time a front end"


# ── What the kept analysis is allowed to answer ─────────────────────────────
#
# Three readers ran a second front end of their own — no cache, no staged
# path, every prelude re-inferred.  The hole scan ran on every rebuild
# whether or not the file contained a single `_` (2.4 s of a 12 s save on
# `quartet.ges`); `--fits` and `--sigs` run when somebody presses `Tab` or
# asks, which is a wait rather than a tax but the same defect.  All three
# ask `pipeline.analysed` now, and what these tests hold is the pair of
# claims that lets them: the kept answer is the *same* answer, and asking
# costs a front end nothing.

HOLED = SYNTH.replace("sine 220.0", "sine _")

#: A definition nobody wrote a signature for, whose inferred one has a
#: **context** — the part `Analysis.constraints` is kept for.
UNSIGNED = "twice x = x + x\n\n" + SYNTH.replace("x * c", "twice (x * c)")


def test_a_hole_is_found_the_same_in_a_kept_analysis():
    """The scan reads SCs that have been through elaboration and
    specialisation rather than stopping at inference, so this is not
    obvious: a hole has to survive those passes carrying its type."""
    from gestate.typecheck import holes_in_source

    forget_analyses()
    cold = holes_in_source(HOLED, rate=RATE)
    assert cold == [(5, 33, "Sig Float")], cold

    analyse(assemble(HOLED, RATE))            # what a rebuild leaves behind
    assert holes_in_source(HOLED, rate=RATE) == cold


def test_a_hole_scan_costs_a_kept_analysis_nothing():
    """Not a timing: `_analyse` is made to fail, so a scan that reaches it
    at all cannot pass.  The point of the door is that a miss is the
    caller's own business and a hit runs no front end."""
    import gestate.pipeline as pipeline
    from gestate.typecheck import holes_in_source

    forget_analyses()
    analyse(assemble(HOLED, RATE))

    def refuse(*_a, **_k):
        raise AssertionError("the hole scan ran a front end of its own")

    ran, pipeline._analyse = pipeline._analyse, refuse
    try:
        assert holes_in_source(HOLED, rate=RATE) == [(5, 33, "Sig Float")]
    finally:
        pipeline._analyse = ran


def test_what_fits_is_the_same_from_a_kept_analysis():
    """Elaboration adds supercombinators and changes no inferred type, so
    the scope a kept analysis offers is the scope inference saw."""
    from gestate.typecheck import fits_in_source

    forget_analyses()
    cold = fits_in_source("Sig Float", SYNTH, rate=RATE)
    assert "cutoff : Sig Float" in cold[0], cold[0][:4]

    analyse(assemble(SYNTH, RATE))
    assert fits_in_source("Sig Float", SYNTH, rate=RATE) == cold


def test_an_offered_signature_keeps_its_context():
    """The one thing `Analysis` did not already carry.  A signature shown
    without its context is one that would not compile if you accepted it,
    so this asserts the `Num` and not merely that the two agree."""
    from gestate.typecheck import signatures_in_source

    forget_analyses()
    cold = signatures_in_source(UNSIGNED, rate=RATE)
    assert list(cold) == ["twice"], cold
    assert "(Num " in cold["twice"], cold["twice"]

    analyse(assemble(UNSIGNED, RATE))
    assert signatures_in_source(UNSIGNED, rate=RATE) == cold


def test_neither_answer_costs_a_kept_analysis_a_front_end():
    import gestate.pipeline as pipeline
    from gestate.typecheck import fits_in_source, signatures_in_source

    forget_analyses()
    analyse(assemble(UNSIGNED, RATE))

    def refuse(*_a, **_k):
        raise AssertionError("it ran a front end of its own")

    ran, pipeline._analyse = pipeline._analyse, refuse
    try:
        assert signatures_in_source(UNSIGNED, rate=RATE)
        assert fits_in_source("Sig Float", UNSIGNED, rate=RATE)[0]
    finally:
        pipeline._analyse = ran


# ── The staged front end ────────────────────────────────────────────────────
#
# `_analyse_staged` answers the library stack from `_stack_front` and
# analyses only the author's part against it.  These pin the property the
# whole design rests on: the staged answer *is* the whole-text answer.


def _case_tags(analysis):
    from collections import Counter

    from gestate.expr import subexprs

    out = {}
    for name, _a, lam, _s in analysis.scs:
        tags = Counter()

        def walk(e):
            alts = getattr(e, "alts", None)
            if alts is not None and hasattr(alts, "keys"):
                for k in alts.keys():
                    tags[k] += 1
            for x in subexprs(e):
                walk(x)

        walk(lam)
        out[str(name)] = tags
    return out


def test_staged_analysis_is_the_whole_text_analysis():
    """Same SC names, same types, same case tags — not merely same sounds.

    The one defect this family of changes can introduce is *two
    numberings in one program*: the cached stack compiled under one tag
    assignment and the author's part under another, which surfaces as a
    `case` meeting a constructor it has no alternative for.
    """
    import gestate.syntax as syn

    src = assemble(SYNTH, RATE)
    forget_analyses()
    staged = analyse(src)
    seam = syn._SEAMS.pop(src)
    forget_analyses()
    try:
        plain = analyse(src)
    finally:
        syn._SEAMS[src] = seam
    assert sorted(str(s[0]) for s in staged.scs) == \
        sorted(str(s[0]) for s in plain.scs)
    assert {k: str(v) for k, v in staged.types.items()} == \
        {k: str(v) for k, v in plain.types.items()}
    assert _case_tags(staged) == _case_tags(plain)


def test_stack_front_survives_a_pickle():
    """The disk store is a pickle round-trip; extraction must not notice.

    The two ways this has actually broken: constraint sites keyed by
    `id()` (a new process, new objects, new ids — dictionaries stopped
    reaching their call sites), and `Nil`/`Cons`/`False`/`True` numbered
    by position (a cached `case` met a `True` built under the other
    numbering).  Extraction exercises both.
    """
    import pickle

    from gestate.pipeline import _STACK_FRONTS, _analysed

    src = assemble(SYNTH, RATE)
    forget_analyses()
    analyse(src)
    (head, front), = _STACK_FRONTS.items()
    round_tripped = pickle.loads(
        pickle.dumps(front, protocol=pickle.HIGHEST_PROTOCOL))
    forget_analyses()
    _STACK_FRONTS[head] = round_tripped
    graph = extract_analysis(analyse(src), rate=RATE)
    assert graph.nodes, "the round-tripped stack front extracted nothing"
