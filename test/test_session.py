"""The editor, driven by names — `spec/workbench.md` acceptance 2.

    `Workbench` and `Session` import no toolkit, and the whole editor
    can be driven in a test with no window: a list of command names in,
    a list of sentences out.

That is not a testing affordance bolted on; it is the ordinary way to
run the thing, because a command *is* a transition and a session *is* a
list of them.  So these tests read as transcripts, which is what
`spec/verification.md` asks of a session one floor down.

Nothing here opens a window, and nothing here plays a sound: the
commands that need a running instrument are exercised against a
`Workbench` in `test_audioeditor.py`, where the pacing player already
lives.  What is checked here is the *layer* — that the list derives,
that every key names a command, that a refusal is a sentence, and that
the arguments are the ones the types promised.
"""

from __future__ import annotations

from gestate.session import KEYS, Detached, Session, Verb, vocabulary


class Bench:
    """A workbench that only remembers what it was told.

    **A stand-in rather than a mock**: it records, it does not assert.
    The point of these tests is what `Session` says, and a double that
    argued back would be a second specification of the model.
    """

    def __init__(self):
        self.log = []
        self.values = {"cutoff": 40, "drive": 0.5}
        self.ranges = {"cutoff": (0, 100), "drive": (0.0, 1.0)}
        self.on = False
        self.keyboard = self
        self.octaves = 0
        self.ends = 32.0

    # what `Session` reaches for
    def apply(self, text, save=True):
        self.log.append(("apply", text, save))

    def audition(self, text):
        self.log.append(("audition", text))

    def toggle(self):
        self.on = not self.on
        return self.on

    def pause(self):
        self.on = False

    def seek_beats(self, beat):
        self.log.append(("seek", beat))

    def set_loop(self, a, b):
        self.log.append(("loop", a, b))

    def clear_loop(self):
        self.log.append(("unloop",))

    #: **The real `Workbench` shape, copied deliberately.**  A stand-in
    #: written to suit the caller teaches the caller a wrong interface:
    #: `has_knob` is a property and `end_beat` a method on the model,
    #: and having them the other way round here is what let `Session`
    #: call both wrongly until `test_session_live.py` said so.
    @property
    def has_knob(self):
        return True

    def end_beat(self):
        return self.ends

    def knob_range(self, name):
        return self.ranges[name]

    def set_value(self, name, value):
        self.values[name] = value

    def learn(self, name):
        return name in self.values

    def listen(self, bank, on):
        self.log.append(("listen", bank, on))

    def transpose(self, by):
        self.octaves += by
        return self.octaves

    def set_seed(self, value):
        self.seed = value

    def roll_seed(self):
        return 4242

    knob_types = {"cutoff": "Int", "drive": "Float"}
    sites = ()


def session(**kw) -> Session:
    return Session(bench=Bench(), **kw)


# ── The list ─────────────────────────────────────────────────────────────


def test_the_palette_is_derived_from_the_language():
    """**The command list is `command.ges`.**  Not a copy of it.

    A capability cannot exist without a name, a type and a sentence,
    because declaring one is what that means — the same reason
    `doc/ref/` cannot drift from the libraries it describes.
    """
    verbs = vocabulary()
    assert len(verbs) > 15, f"only {len(verbs)} commands"
    names = {v.name for v in verbs}
    for expected in ("apply", "play", "loop", "set", "quit"):
        assert expected in names
    for v in verbs:
        assert v.summary, f"{v.name} has no sentence"
        assert v.summary.endswith("."), f"{v.name}'s summary is not a sentence"


def test_the_types_say_what_a_command_wants():
    """The dividend of the vocabulary being a *typed* language: the view
    can ask for the right thing without being told separately."""
    by = {v.name: v for v in vocabulary()}
    assert by["apply"].args == ()
    assert by["seek"].args == ("Int",)
    assert by["loop"].args == ("Int", "Int")
    # **`Named` and a type variable.**  The checker resolves the `a`
    # from the name in the first argument — an `Int` knob takes an
    # `Int` — and the palette cannot and does not need to.
    assert by["set"].args == ("Named", "a")
    assert by["listen"].args == ("Named",)
    assert by["find"].args == ("Text",), "search takes text, not a name"
    assert by["goto"].args == ("Named",), "and goto takes a name, not text"
    # And it reads as a usage line for free.
    assert str(by["loop"]) == "loop <int> <int>"
    assert str(by["set"]) == "set <named> <value>"
    assert str(by["apply"]) == "apply"


def test_a_combinator_is_not_a_palette_entry():
    """`andThen` takes commands, so it cannot be picked from a list —
    there is no box to type a command into.  Derived from its type
    rather than kept on a list of exceptions."""
    assert "andThen" not in {v.name for v in vocabulary()}


def test_every_key_names_a_command():
    """**A key with no command cannot exist.**  One vocabulary, or the
    list stops being the answer to "what can this do"."""
    names = {v.name for v in vocabulary()}
    for key, name in ((k, n) for n, k in KEYS.items()):
        assert name in names, f"{key} names `{name}`, which is not a command"
    # And the list carries the key, so reading one teaches the other.
    by = {v.name: v for v in vocabulary()}
    assert by["apply"].key == "Ctrl-S"
    assert by["stop"].key == "", "not every command needs a key"


def test_every_declared_command_is_implemented_and_the_reverse():
    """A signature and its implementation are two different things, so a
    *check* is the right tool — unlike two copies of the same data,
    where the right tool is deriving one from the other."""
    declared = {v.name for v in vocabulary()}
    done = {n[3:] for n in dir(Session) if n.startswith("do_")}
    assert declared - done == set(), f"declared, not implemented: {declared - done}"
    assert done - declared == set(), f"implemented, not declared: {done - declared}"


# ── Running them ─────────────────────────────────────────────────────────


def test_a_transcript_of_names_reads_as_what_it_did():
    s = session()
    said = [s.run(*c) for c in [
        ("play",), ("loop", 1, 5), ("set", "cutoff", 70), ("loopOff",),
        ("play",), ("octave", -1),
    ]]
    assert said == [
        "playing",
        "looping bars 1-5",
        "cutoff = 70",
        "not looping",
        "stopped",
        "octave -1",
    ]
    assert s.said == said, "everything said is kept, newest last"


def test_bars_count_from_one_where_a_person_is_concerned():
    """A transport counts beats from zero; a musician counts bars from
    one.  The conversion lives in one place so nothing else has to know
    it."""
    s = session()
    s.run("seek", 1)
    s.run("loop", 3, 5)
    assert s.bench.log == [("seek", 0.0), ("loop", 8.0, 16.0)]


# ── Refusals ─────────────────────────────────────────────────────────────


def test_a_refusal_is_a_sentence_not_an_exception():
    """Everything here is reached from a palette somebody is typing
    into, so a wrong name is an ordinary event and the answer is a line
    they can read."""
    s = session()
    assert s.run("nonesuch") == "no command `nonesuch`"
    assert s.run("loop") == "`loop` takes loop <int> <int>"
    assert s.run("apply", 1) == "`apply` takes no arguments"
    assert s.run("set", "nope", 1.0) == "no parameter `nope`"
    assert s.run("loop", 5, 2) == "bar 2 is not after bar 5"


def test_a_workbench_that_throws_is_still_a_sentence():
    """A traceback in somebody's terminal is not an answer, and this
    layer sits between a person and a machine that is playing music."""
    s = session()

    def boom(*_a, **_k):
        raise RuntimeError("the engine said no")

    s.bench.apply = boom
    assert s.run("apply") == "apply: the engine said no"


def test_a_value_outside_a_knobs_range_is_clamped_and_said_so():
    """Clamping silently would be a control that lies about where it
    is; refusing would be a knob you cannot turn to the end."""
    s = session()
    assert s.run("set", "cutoff", 140) == "cutoff = 100 (clamped from 140)"
    assert s.bench.values["cutoff"] == 100


# ── The view is somebody else's ──────────────────────────────────────────


def test_without_a_window_the_window_commands_say_so():
    """**A refusal that reads**, rather than an attribute error.  Half
    the list is about the window, and a headless session must be able to
    run all of it and be told which ones it cannot do."""
    s = session()
    assert s.run("undo") == "nothing to undo"
    assert s.run("redo") == "nothing to redo"
    assert s.run("find", "sine") == "no `sine`"
    assert s.run("zoomIn") == "as big as it goes"
    assert s.run("canvas") == "this file draws nothing"


def test_the_view_owns_the_text_and_the_undo():
    """`spec/editor.md` requires undo to be *text* undo, so the thing
    holding the text is the thing that owns it — this layer only asks."""

    class Window(Detached):
        def __init__(self):
            self.body = "sound : Sig Float\n"
            self.undone = 0

        def text(self):
            return self.body

        def undo(self):
            self.undone += 1
            return True

        def find(self, pattern):
            return self.body.find(pattern)

    view = Window()
    s = session(view=view)
    assert s.run("apply") == "applying"
    assert s.bench.log[-1] == ("apply", "sound : Sig Float\n", True)
    assert s.run("undo") == "undone"
    assert view.undone == 1
    assert s.run("find", "Sig") == "found `Sig`"
    assert s.run("find", "nope") == "no `nope`"


def test_the_session_imports_no_toolkit():
    """Acceptance 2's other half, checked rather than promised."""
    import gestate.session as mod

    source = open(mod.__file__).read()
    for toolkit in ("import tkinter", "import pygame", "from tkinter",
                    "from pygame"):
        assert toolkit not in source, f"session.py reaches for {toolkit}"


def test_every_command_can_be_run_headless_without_raising():
    """The whole list, once each, with the arguments its types ask for.

    A command that could only be reached through a window would be one
    this test could not name — which is the point of the list being the
    only way in.
    """
    s = session()
    sample = {"Int": 1, "Float": 0.5, "Text": "sine",
              "Named": "cutoff", "a": 0.5}
    for verb in vocabulary():
        args = tuple(sample[a] for a in verb.args)
        said = s.run(verb.name, *args)
        assert isinstance(said, str) and said, f"{verb.name} said nothing"


def test_the_palette_ranks_a_name_above_a_sentence():
    """Somebody typing `loop` wants `loop`, not a command whose summary
    happens to mention looping.

    The rule is `audiopygame`'s reference-browser ranking, which is the
    part of that browser with a decision in it — the rest was chrome
    over a generated index.
    """
    s = session()
    names = [v.name for v in s.matching("loop")]
    assert names[:3] == ["loop", "loopAll", "loopOff"], names
    # `play`'s summary says "or stop it if it is running", so a prose
    # match exists and must come after every name match.
    stop = [v.name for v in s.matching("stop")]
    assert stop[0] == "stop"
    assert "play" in stop and stop.index("play") > 0

    # An empty query is the whole list, in the order the file declares.
    assert [v.name for v in s.matching("")] == [v.name for v in vocabulary()]
    # And nothing matching is nothing, not everything.
    assert s.matching("zzzz") == []


# ── What the vocabulary bought ───────────────────────────────────────────


def test_find_takes_text_and_goto_takes_a_name():
    """**Two commands, not one.**  Search matters most when you are
    looking for something that is *not* a name yet — a typo you are
    fixing, half a word, a fragment of a comment — so typing it as a
    name would remove the tool where it is wanted."""
    class Window(Detached):
        def __init__(self):
            self.went = None

        def find(self, pattern):
            return 3 if pattern == "sin" else -1

        def goto(self, row):
            self.went = row
            return True

    class Sited:
        pass

    view = Window()
    s = session(view=view)
    # A fragment that is nobody's name is still findable.
    assert s.run("find", "sin") == "found `sin`"
    # And `goto` answers about declarations, which the workbench knows
    # from `audiospans` — the same fact that puts a knob in the margin.
    site = Sited()
    # `audiospans.Site` counts lines from **one** — "the convention a
    # text widget wants" — so nothing here adds to it.
    site.name, site.line = "cutoff", 13
    s.bench.sites = [site]
    assert s.run("goto", "cutoff") == "line 13"
    assert view.went == 13
    assert s.run("goto", "nowhere") == "no declaration `nowhere`"


def test_what_answers_from_the_compiler():
    """The compiler answering, rather than a documentation lookup."""
    s = session()
    assert s.run("what", "cutoff") == "cutoff : Chan Int"
    assert s.run("what", "drive") == "drive : Chan Float"
    assert s.run("what", "nobody") == "no declaration `nobody`"


def test_performing_says_what_a_played_note_does():
    """**Not a mode of the editor.**  It changes what happens to a
    *note*, not what a *key* means — the letters go on typing."""
    s = session()
    assert s.performing == "on", "notes sound until told otherwise"
    assert s.run("performStep") == "notes sound and are written"
    assert s.performing == "step"
    assert s.run("performOff") == "notes go nowhere"
    assert s.run("performOn") == "notes sound"
    assert s.performing == "on"


def test_a_seed_is_typed_and_a_reroll_is_pressed():
    """Two gestures, not one: rolling is what you press while looking,
    typing a seed is what you do once you have found one to keep."""
    s = session()
    assert s.run("seed", 7) == "seed 7"
    assert s.bench.seed == 7
    assert s.run("reroll") == "seed 4242"
    assert s.bench.seed == 4242


def test_skip_is_a_command_like_any_other():
    """The identity of `++`.  In the palette because hiding it would be
    a special case: composing is the point, and the thing that composes
    with everything and changes nothing belongs beside the things that
    do."""
    s = session()
    assert s.run("skip") == "nothing"
    assert "skip" in {v.name for v in vocabulary()}


def test_the_constraint_is_enforced_where_it_matters():
    """`listen` on a bank whose payload has no `FromMIDI` instance is
    refused *by the checker*, not by a sentence at run time.

    This is the dividend of the vocabulary being a typed language, and
    it is checked here because `command.ges` alone cannot show it — the
    refusal happens where a command is written against a program.
    """
    from gestate.pipeline import compile as _compile

    base = ("class Fc a where\n    fc : Int -> a\n"
            "instance Fc Float where\n    fc v = toFloat v\n"
            "C := S\n"
            "N a := TheName (List Char)\n"
            "use : (Fc a) => N a -> C\nuse n = S\n")
    _compile(base + "ok : N Float -> C\nok n = use n\n")
    try:
        _compile(base + "bad : N Int -> C\nbad n = use n\n")
    except Exception as e:
        assert "No instance" in str(e), e
    else:
        raise AssertionError("a name of the wrong kind was accepted")
