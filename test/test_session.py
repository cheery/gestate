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

from gestate.session import (KEYS, Detached, Session, Verb, act,
                             furniture, vocabulary)


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


class _Site:
    """A declaration site, as `audiospans` reports one."""

    def __init__(self, name, line):
        self.name, self.line = name, line


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


# ── The wire ─────────────────────────────────────────────────────────────


def test_the_furniture_is_a_reading_of_facts_the_model_already_keeps():
    """Nothing in the description is a second copy: `sites` is what puts
    a knob beside its declaration, `values` is what a knob holds, and
    `trouble` is the last complaint."""
    from gestate.session import furniture

    class Site:
        def __init__(self, name, line):
            self.name, self.line = name, line

    s = session()
    s.bench.sites = [Site("cutoff", 40), Site("drive", 44)]
    s.bench.trouble = "expected a type, got `sound` (at 12:8-12:11)"
    s.run("play")

    lines = furniture(s).splitlines()
    assert lines[0] == "status\tplaying"
    assert "trouble\t12\texpected a type, got `sound` (at 12:8-12:11)" in lines
    assert "knob\tcutoff\t40\t40\t0\t100\tInt" in lines
    assert "knob\tdrive\t44\t0.5\t0.0\t1.0\tFloat" in lines
    assert any(line.startswith("play\t") for line in lines)
    # And every command, so the palette has something to show.
    assert sum(1 for line in lines if line.startswith("command\t")) == \
        len(s.commands())


def test_a_gesture_is_a_verb_and_literals():
    """The other half of the wire, and the same shape.  An unknown verb
    is a sentence rather than an exception."""
    from gestate.session import act

    s = session()
    assert act(s, "command\tplay") == "playing"
    assert act(s, "turn\tcutoff\t70") == "cutoff = 70"
    assert act(s, "edited") == ""
    assert act(s, "wobble\t1") == "no gesture `wobble`"
    assert act(s, "turn\tcutoff\tnope") == "turn: `nope` is not a number"


def test_filtering_is_answered_by_the_model():
    """**The ranking has one home.**  The window asks; it does not
    sort — a second implementation there would be two copies of one
    decision."""
    from gestate.session import act

    s = session()
    said = act(s, "filter\tloop")
    assert said.startswith("3 of "), said
    assert [v.name for v in s.filtered][:3] == ["loop", "loopAll", "loopOff"]
    # **An empty query is not a filter that matched everything.**  It
    # is no filter at all, and the two are different: one shows the
    # whole list, the other could legitimately show none of it.
    act(s, "filter\t")
    assert s.filtered is None
    assert len(s.palette_list()) == len(s.commands())
    # And a query nothing matches shows nothing, rather than everything.
    act(s, "filter\tzzzz")
    assert s.filtered == []
    assert s.palette_list() == []


def test_a_played_note_obeys_what_performing_says():
    """**The one place `performing` is read**, so every caller is spared
    asking."""
    from gestate.session import act

    played = []

    class Keys:
        def press(self, n):
            played.append(("on", n))

        def release(self, n):
            played.append(("off", n))

    s = session()
    s.bench.keyboard = Keys()
    s.run("performOff")
    act(s, "note\t60\t1")
    assert played == [], "notes go nowhere"

    s.run("performOn")
    act(s, "note\t60\t1")
    act(s, "note\t60\t0")
    assert played == [("on", 60), ("off", 60)]


# --- the loop's pacing -------------------------------------------------
#
# The command list is filtered by the model, so a keystroke in it costs a
# round trip through `run`'s loop.  How long that loop sleeps *is* how
# far the list trails your hand, which makes these two constants part of
# the interface rather than a tuning detail.

def test_pace_hurries_while_a_hand_is_moving():
    from gestate.workbench import BUSY, pace
    assert pace(True, 0.010) == BUSY
    # A round trip is a poll plus a frame.  Fifteen milliseconds of frame
    # leaves no room for a thirty-millisecond poll.
    assert BUSY <= 0.005


def test_pace_does_not_spin_on_a_moving_beat():
    """The description differs every tick while the transport runs.

    Pacing on *that* rather than on gestures would hold the fast pace
    forever — a core spun to keep a number looking smooth.  So an
    unstirred tick must back off, all the way, on its own.
    """
    from gestate.workbench import IDLE, pace
    wait = pace(True, IDLE)
    for _ in range(10):
        wait = pace(False, wait)
    assert wait == IDLE


def test_pace_backs_off_gradually():
    """People type in bursts; the second letter should not pay for the
    first having finished."""
    from gestate.workbench import BUSY, IDLE, pace
    after_one_quiet_tick = pace(False, BUSY)
    assert BUSY < after_one_quiet_tick < IDLE


def test_closing_the_list_stops_filtering():
    """A shut command list has no query.

    Without this the description goes on carrying the three commands the
    last query matched, and the next Ctrl-K opens onto the answer to a
    question nobody asked.
    """
    it = session()
    act(it, "filter\tloop")
    assert len(it.palette_list()) < len(it.commands())
    act(it, "filter\t")                       # what closing sends
    assert it.filtered is None
    assert it.palette_list() == it.commands()


# ── Commands that are the window's ───────────────────────────────────────
#
# Undo, the zoom and the caret are the window's own state and live on the
# window's thread.  A command reaches them by leaving an *order*, and
# answers from a mirror the window volunteers — never by calling across.

class Editor:
    """The ABI, remembering what it was ordered to do."""

    def __init__(self, text: str = "one\ntwo\nthree\n"):
        self.text = text
        self.orders: list = []

    def order(self, line: str) -> None:
        self.orders.append(line)

    def request_close(self) -> None:
        pass


def a_window(text: str = "one\ntwo\nthree\n"):
    from gestate.workbench import Window

    ed = Editor(text)
    return Window(ed), ed


def test_zoom_orders_the_window_and_stops_at_the_ends():
    win, ed = a_window()
    win.note_state(zoom=0, rungs=3, undos=0, redos=0)
    assert win.zoom(-1) is False, "already as small as it goes"
    assert ed.orders == []
    assert win.zoom(1) is True
    assert win.zoom(1) is True
    assert win.zoom(1) is False, "already as big as it goes"
    assert ed.orders == ["zoom\t1", "zoom\t1"]


def test_undo_answers_from_the_mirror():
    """**Immediately, and honestly.**  `undo` has to say which of the two
    sentences it is the instant it runs; it cannot wait a frame."""
    win, ed = a_window()
    win.note_state(zoom=0, rungs=9, undos=0, redos=0)
    assert win.undo() is False
    assert ed.orders == []
    win.note_state(zoom=0, rungs=9, undos=2, redos=0)
    assert win.undo() is True
    assert win.redo() is True, "undoing made something to redo"
    assert ed.orders == ["undo", "redo"]


def test_find_searches_the_text_and_moves_the_caret():
    """The model holds a copy of the document, so the search is a fact it
    can establish; only moving the caret has to be an order."""
    win, ed = a_window("alpha\nbeta\ngamma\n")
    assert win.find("gamma") == 3
    assert ed.orders == ["goto\t3"]
    assert win.find("nowhere") == -1


def test_goto_refuses_a_line_the_file_does_not_have():
    win, ed = a_window("alpha\nbeta\n")
    assert win.goto(9) is False
    assert win.goto(0) is False
    assert ed.orders == []
    assert win.goto(2) is True
    assert ed.orders == ["goto\t2"]


def test_the_state_gesture_reaches_the_view():
    win, _ed = a_window()
    it = session()
    it.view = win
    act(it, "state\t4\t9\t3\t1")
    assert (win.zoom_at, win.zoom_rungs, win.undos, win.redos) == (4, 9, 3, 1)


def test_zoom_commands_run_end_to_end():
    """What the palette does when `zoomIn` is picked."""
    win, ed = a_window()
    it = session()
    it.view = win
    act(it, "state\t0\t3\t0\t0")
    assert it.run("zoomIn") == "bigger"
    assert it.run("zoomOut") == "smaller"
    assert it.run("zoomOut") == "as small as it goes"
    assert ed.orders == ["zoom\t1", "zoom\t-1"]


# ── Commands that take arguments ─────────────────────────────────────────
#
# Eleven of the twenty-nine do.  None of them were reachable from the
# list until it could *ask*, which is what `spec/workbench.md` means by
# "the types are what let the view ask".

def test_arguments_arrive_as_text_and_are_read_as_declared():
    """Everything from a palette is text; the signature is what knows
    `seek` wants a number."""
    it = session()
    assert it.run("seek", "4") == "at bar 4"
    assert it.run("loop", "2", "6") == "looping bars 2-6"
    assert it.run("octave", "1") == "octave 1"


def test_a_number_that_is_not_one_is_a_sentence():
    it = session()
    assert it.run("seek", "soon") == "seek: `soon` is not a whole number"


def test_the_palette_says_what_each_command_takes():
    it = session()
    lines = furniture(it).splitlines()
    said = {l.split("\t")[1]: l.split("\t")[5]
            for l in lines if l.startswith("command\t")}
    assert said["loop"] == "Int,Int"
    assert said["listen"] == "Named"
    assert said["stop"] == "", "a command that takes nothing says so"


def test_asking_about_a_named_argument_offers_names():
    it = session()
    it.bench.sites = (_Site("cutoff", 12), _Site("pitch", 30))
    it.bench.knob_types = {"cutoff": "Float", "pitch": "Int"}
    assert act(it, "wants\tlisten\t0\t") == "2 name(s)"
    assert [n for n, _note in it.choices()] == ["cutoff", "pitch"]
    lines = furniture(it).splitlines()
    assert "choice\tcutoff\tChan Float" in lines


def test_names_are_ranked_the_way_commands_are():
    it = session()
    it.bench.sites = (_Site("cut", 1), _Site("cutoff", 2), _Site("uncut", 3))
    it.bench.knob_types = {}
    assert [n for n, _ in it.naming("cut")] == ["cut", "cutoff", "uncut"]


def test_a_number_argument_is_typed_not_chosen():
    """Offering a list of numbers would be a menu of guesses."""
    it = session()
    it.bench.sites = (_Site("cutoff", 12),)
    act(it, "wants\tseek\t0\t")
    assert it.choices() == []


def test_the_window_can_say_it_has_stopped_asking():
    it = session()
    act(it, "wants\tlisten\t0\tcut")
    assert it.asking is not None
    act(it, "asked")
    assert it.asking is None
    assert it.choices() == []


def test_an_unfiltered_list_is_not_news():
    """The window clears the filter after running a command.

    A count answered for that would land in the status line *after* the
    command's own sentence and hide it: you would pick `seek`, it would
    work, and the line would read "29 of 29".
    """
    it = session()
    assert act(it, "filter\tloop") == "3 of 29"
    assert act(it, "filter\t") == ""
    assert it.filtered is None


def test_a_command_keeps_the_last_word():
    it = session()
    it.run("seek", "8")
    act(it, "asked")
    act(it, "filter\t")                      # what closing sends
    said = furniture(it).splitlines()[0]
    assert said == "status\tat bar 8", said


class _Transport:
    def __init__(self, playing):
        self.playing = playing
        self.loop = None


def test_playing_means_the_beat_is_moving_not_the_thread_is_alive():
    """`Workbench.playing` asks whether the audio *thread* is alive — a
    different question wearing the same word, and true while stopped."""
    it = session()
    it.bench.playing = True                  # the thread is up …
    it.bench.transport = _Transport(False)   # … and time is not moving
    assert "play\t0\t" in furniture(it)
    it.bench.transport.playing = True
    assert "play\t1\t" in furniture(it)


def test_every_shortcut_takes_control():
    """There is one mode and you are typing in it, so a bare key is text.

    `play` was advertised as `Space` for a while, inherited from a window
    where the piano had the focus.  In an editor that is either a
    shortcut that never fires or an editor you cannot type a space into.
    """
    bare = {name: key for name, key in KEYS.items()
            if not key.startswith("Ctrl-")}
    assert bare == {}, f"these could not work in a text editor: {bare}"


def test_a_shortcut_reaches_the_window_as_the_list_spells_it():
    """The window matches the chord against the key each command
    advertises, so the two cannot drift.  This holds the spelling."""
    it = session()
    advertised = {l.split("\t")[1]: l.split("\t")[3]
                  for l in furniture(it).splitlines()
                  if l.startswith("command\t")}
    assert advertised["find"] == "Ctrl-F"
    assert advertised["apply"] == "Ctrl-S"
    assert advertised["play"] == "Ctrl-Space"
