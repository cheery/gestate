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

    def say(self, message):
        """What a worker reports when it lands — `Workbench.say`.

        Here because the export commands answer twice: once at once, and
        once from the thread doing the work.  A double without it turned
        the second answer into an exception on a daemon thread, which
        pytest reports as a warning and a person would never see at all.
        """
        self.log.append(("say", message))

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
              "Named": "cutoff", "a": 0.5,
              # A name that is certainly not there, so `open` and
              # `steal` answer without touching the disk.
              "Path": "no-such-file.ges",
              # A real one, so `template` gets as far as the view and
              # answers that a detached session has nowhere to put it —
              # which is the refusal this sweep exists to hear.
              "Template": "knob",
              # And a no, so `overwrite` answers without an export
              # having been asked for.
              "Answer": "no"}
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


class _Written:
    """A view holding source, which is what `fits` asks the compiler about."""

    SYNTH = ("cutoff : Sig Float\n"
             "cutoff = mkKnob 0.4\n"
             "\n"
             "sound : Sig Float\n"
             "sound = 0.2 * sine 220.0\n")

    def __init__(self, text=None):
        self._text = self.SYNTH if text is None else text
        self.showing = "source"

    def text(self):
        return self._text


def test_fits_answers_about_the_text_in_the_window():
    """**The unsaved program is the one the question is about.**

    `--fits` from the shell reads a file; a person asking in the editor
    is asking about what is in front of them, including the line they
    have not saved.  So this drives the real compiler over the view's
    text, and the answer names the file's *own* declarations — which is
    the half `--fits` on the saved file could not have known.
    """
    s = session(view=_Written())
    said = s.run("fits", "Sig Float")
    assert said.endswith("fit Sig Float"), said
    page = "\n".join(s.page)
    assert "what fits Sig Float:" in page
    assert "cutoff : Sig Float" in page, "the file's own names are the point"
    assert "sound : Sig Float" in page


def test_fits_reports_a_file_that_does_not_compile():
    """Mid-line is the ordinary case, so the complaint *is* the answer.

    Answering "nothing fits" about a file that never got as far as
    inference would be the `canvas` defect again — a fact about the
    clock reported as a fact about the program.
    """
    s = session(view=_Written("sound : Sig Float\nsound = ((\n"))
    said = s.run("fits", "Sig Float")
    assert said == "fits Sig Float: the file does not compile"
    assert s.page and "what fits Sig Float:" in s.page[0]


def test_fits_with_no_type_asks_rather_than_guessing():
    """A type is typed, not chosen — there is no list of every type."""
    s = session(view=_Written())
    assert s.run("fits", "") == "fits: which type?"
    assert s.run("fits", "   ") == "fits: which type?"


class _Inserting:
    """A view that remembers what was put into it."""

    def __init__(self):
        self.showing = "source"
        self.put = []

    def text(self):
        return ""

    def insert(self, text):
        self.put.append(text)
        return True


def test_template_inserts_the_program_and_not_the_prose():
    """**The documentation stays behind**, which is the whole rule.

    A template's header is written to be read in the list — it says what
    the idea is and why it is spelled that way — and pasting it would put
    somebody else's explanation into a file where it goes stale the
    moment the line under it changes.
    """
    view = _Inserting()
    s = session(view=view)
    assert s.run("template", "knob") == "inserted `knob`"
    put = view.put[0]
    assert "mkKnob" in put, "the program is the point"
    assert "#" not in put, f"a comment was pasted: {put!r}"
    # And the reasoning is still readable, on the page rather than in the
    # file — which is where it was worth having in the first place.
    assert s.page and "knob" in s.page[0]
    assert any("control rate" in line.lower() for line in s.page)


def test_a_second_return_keeps_the_template_instead_of_pasting_it_twice():
    """**Return again means done, not again.**

    A finished call repeats on Return — the next match, the next take —
    which is right for `find` and wrong here, where again is a second
    copy of the same code pasted under the first.
    """
    view = _Inserting()
    view.closed = False
    view.close_list = lambda: setattr(view, "closed", True) or True
    s = session(view=view)
    assert s.run("template", "knob") == "inserted `knob`"
    assert s.run("template", "knob") == "kept `knob`"
    assert len(view.put) == 1, "the template was pasted twice"
    assert view.closed, "the dialog stayed open"


def test_escape_takes_a_pasted_template_back():
    """`Esc` out of a dialog means *never mind*, and for a paste that is
    taking it back.  One insert is one edit, so one undo is exact."""
    view = _Inserting()
    view.undone = 0
    view.undo = lambda: (setattr(view, "undone", view.undone + 1), True)[1]
    s = session(view=view)
    s.run("template", "knob")
    assert act(s, "shut") == "undid `knob`"
    assert view.undone == 1
    # And only once — a second `shut` has nothing standing.
    assert act(s, "shut") == ""
    assert view.undone == 1


def test_backspacing_out_of_a_template_takes_it_back_too():
    """**A cancel is a cancel, whichever key it was.**

    The palette steps back an argument and asks again, which is the same
    *never mind* `Esc` means — and the rule the dialog is built on is
    that a template you did not keep does not come out.
    """
    view = _Inserting()
    view.undone = 0
    view.undo = lambda: (setattr(view, "undone", view.undone + 1), True)[1]
    s = session(view=view)
    s.run("template", "knob")
    act(s, "wants\ttemplate\t0\t")
    assert view.undone == 1, "backing out left the paste behind"
    assert s.said[-1] == "undid `knob`"
    # Backing out of some other command's argument is not about this.
    s.run("template", "knob")
    act(s, "wants\tfind\t0\t")
    assert view.undone == 1


def test_doing_something_else_settles_a_pasted_template():
    """Undoable while it is the thing you are looking at, and not after.

    An `Esc` three commands later taking back a paste you had forgotten
    about would be the editor undoing your work behind you.
    """
    view = _Inserting()
    view.undone = 0
    view.undo = lambda: (setattr(view, "undone", view.undone + 1), True)[1]
    s = session(view=view)
    s.run("template", "knob")
    s.run("play")
    act(s, "shut")
    assert view.undone == 0, "a settled template was undone anyway"


def test_template_refuses_by_name():
    view = _Inserting()
    s = session(view=view)
    assert s.run("template", "nosuch") == "no template `nosuch`"
    assert s.run("template", "") == "template: which one?"
    assert view.put == [], "a refusal put nothing in the file"


def test_a_template_argument_offers_the_directory():
    """`Template` is its own type so that the list can appear — the rule
    `Named` and `Path` already follow."""
    s = session()
    s.asking = ("template", 0, "")
    offered = {name for name, _note in s.choices()}
    assert {"knob", "voices"} <= offered
    # Ranked, and the summary is searched too: somebody reaching for a
    # snippet remembers what it does sooner than what it is called.
    s.asking = ("template", 0, "polyphonic")
    assert s.choices()[0][0] == "voices"


class _Editing:
    """A view holding text that a command may replace."""

    def __init__(self, text):
        self._text = text
        self.showing = "source"

    def text(self):
        return self._text

    def replace(self, text):
        self._text = text
        return True


MESSY = "a : Int\na  =   1\n\nb : Int\nb   =    2\n"


def test_fmtAll_lays_out_the_whole_file():
    view = _Editing(MESSY)
    s = session(view=view)
    assert s.run("fmtAll") == "laid out the file"
    # The blank line the author left between them is theirs, and stays.
    assert view._text == "a : Int\na = 1\n\nb : Int\nb = 2\n"
    # **Idempotent, and it says so rather than doing nothing quietly.**
    assert s.run("fmtAll") == "already laid out"


def test_fmt_takes_whole_declarations_and_says_which():
    """A range landing in a body widens to the declaration around it.

    Half a declaration is not something the parser can lay out, so the
    only honest choices are to widen or to refuse — and widening while
    *saying* what was taken is the one that does what somebody meant.
    """
    view = _Editing(MESSY)
    s = session(view=view)
    assert s.run("fmt", 5, 5) == "laid out lines 4-5"
    assert "a  =   1" in view._text, "the other declaration was not touched"
    assert "b = 2" in view._text


def test_fmt_says_when_a_range_holds_no_declaration():
    view = _Editing(MESSY)
    s = session(view=view)
    assert s.run("fmt", 3, 3) == "fmt: no declaration on lines 3-3"
    assert view._text == MESSY, "a refusal changed the file"


def test_inferAll_writes_the_types_the_compiler_already_knows():
    """The compiler inferred these to compile the file; this writes them
    down.  A signature somebody typed is left alone — the author's
    spelling is the authority."""
    view = _Editing("cutoff = mkKnob 0.4\n\n"
                    "sound : Sig Float\nsound = 0.2 * sine 220.0\n")
    s = session(view=view)
    assert s.run("inferAll") == "wrote `cutoff`'s signature"
    assert view._text.startswith("cutoff : ")
    assert view._text.count("sound : Sig Float") == 1, "an authored one moved"
    assert s.run("inferAll") == "every declaration already has a signature"


def test_infer_tells_a_missing_name_from_an_annotated_one():
    """`canvas`'s lesson: two different facts need two different answers."""
    view = _Editing("sound : Sig Float\nsound = 0.2 * sine 220.0\n")
    s = session(view=view)
    assert s.run("infer", "sound") == "`sound` already has a signature"
    assert s.run("infer", "nobody") == "no declaration `nobody`"
    assert s.run("infer", "") == "infer: which declaration?"


def test_an_export_asks_before_it_overwrites(tmp_path):
    """**Asked, not refused** — which is where this parts from `steal`.

    Writing over the plugin you exported an hour ago is the ordinary
    thing; refusing it would make the command useless exactly when it is
    working.  So the question is asked, and the palette shows two rows.
    """
    taken = tmp_path / "already.wav"
    taken.write_text("not really a wav")
    view = _Editing("sound : Sig Float\nsound = 0.2 * sine 220.0\n")
    s = session(view=view)
    s.bench.path = tmp_path / "synth.ges"
    said = s.run("exportWav", str(taken))
    assert said == "already.wav exists — you want to overwrite? [y/n]"
    assert s.asking == ("overwrite", 0, "")
    # The two rows, and `y`/`n` filter to one — `[y/n]` at the keyboard
    # without an inline prompt, which would be a second mode.
    assert [r[0] for r in s.choices()] == ["yes", "no"]
    s.asking = ("overwrite", 0, "n")
    assert [r[0] for r in s.choices()] == ["no"]
    # And a no leaves the file exactly as it was.
    assert s.run("overwrite", "no") == "left already.wav alone"
    assert taken.read_text() == "not really a wav"


def test_a_yes_does_not_stand_for_the_next_time(tmp_path):
    """**A confirmation must never become standing consent.**

    The answer is cleared before the export starts, so exporting over the
    same name again asks again.  Left set, the first yes would answer
    every later export to that file silently — which is the one thing a
    question like this must not do.
    """
    taken = tmp_path / "again.wav"
    taken.write_text("x")
    s = session(view=_Editing("sound : Sig Float\nsound = sine 220.0\n"))
    s.bench.path = tmp_path / "synth.ges"
    # **The confirmation is what is under test, not the renderer.**  A
    # real render here would be eight seconds of audio to check a field
    # is cleared, and `test_templates.py` already builds what compiles.
    started = []
    s._start_export = lambda kind, want: started.append((kind, want)) or "go"
    s.run("exportWav", str(taken))
    assert s.confirming is not None
    s.run("overwrite", "yes")
    assert s.confirming is None, "the yes was left standing"
    # And the next one asks, rather than going straight through.
    assert s.run("exportWav", str(taken)).endswith("[y/n]")


class _AtCaret:
    """A view standing at a character offset, which can be filled."""

    def __init__(self, text, at):
        self._text, self._at = text, at
        self.showing = "source"
        self.filled = None

    def text(self):
        return self._text

    def caret(self):
        return self._at

    def fill(self, text):
        self.filled = text
        return True


HOLED = "sound : Sig Float\nsound = _ * sine 220.0\n"
_START = len("sound : Sig Float") + 1 + 8          # the `_` itself


def test_a_hole_is_found_from_either_end_of_it():
    """**Both ends, because both are where a hand leaves the caret.**

    You arrow onto a `_` and stop before it, or you delete what was there
    and stop after it.  Insisting on one would make the affordance work
    half the times it is reached for, which is worse than not having it.
    """
    from gestate.typecheck import holes_in_source

    holes = holes_in_source(HOLED)
    assert holes == [(2, 8, "Sig Float")]
    for at, where in ((_START, "on it"), (_START + 1, "just after")):
        s = session(view=_AtCaret(HOLED, at))
        s.bench.holes = holes
        assert s.hole_at_caret() == "Sig Float", where
    s = session(view=_AtCaret(HOLED, _START - 5))
    s.bench.holes = holes
    assert s.hole_at_caret() is None, "a caret nowhere near it"


def test_fits_at_a_hole_answers_without_being_told_the_type():
    """Inference already knows what belongs there; retyping the
    compiler's own answer is the affordance failing where it is most
    wanted."""
    from gestate.typecheck import holes_in_source

    view = _AtCaret(HOLED, _START)
    s = session(view=view)
    s.bench.holes = holes_in_source(HOLED)
    said = s.run("fits", "")
    assert said.endswith("fit Sig Float"), said
    assert s.page and "what fits Sig Float:" in s.page[0]


def test_the_margin_joins_the_holes_on_one_line():
    """One row per line, not per hole — the margin has one row to say
    them in, and which of several things to say there is a decision."""
    s = session()
    s.bench.holes = [(5, 17, "Float"), (5, 8, "Sig Float"), (9, 4, "Int")]
    rows = [l for l in furniture(s).splitlines() if l.startswith("hole\t")]
    # Ordered by column within the line, because that is the reading order.
    assert rows == ["hole\t5\t_ : Sig Float, _ : Float", "hole\t9\t_ : Int"]


class _Filling:
    """A view that fills its box the way the window does."""

    def __init__(self, path):
        self.showing = "source"
        self.box = ""
        self.fills = 0

    def text(self):
        return "sound : Sig Float\nsound = sine 220.0\n"

    def caret(self):
        return 0

    def fill(self, text):
        self.box = text
        self.fills += 1
        return True


def test_an_export_pins_its_name_and_leaves_the_box_empty(tmp_path):
    """**Marked, not typed** — the rule `open` already follows.

    Filling the box made it impossible to clear: backspace emptied it,
    the model filled it straight back in, and backspace-on-empty — which
    is how you step *out* of a question — could never be reached.  A row
    has no such failure mode: the box stays empty, the row is one Return
    away, and the first letter typed is a new name.
    """
    view = _Filling(tmp_path)
    s = session(view=view)
    s.bench.path = tmp_path / "demo.ges"
    (tmp_path / "other.wav").write_text("x")

    act(s, "wants\texportWav\t0\t")
    assert view.fills == 0, "nothing should be typed into the box"
    rows = s.choices()
    assert rows[0][0] == "demo.wav", "the proposal is not at the top"
    assert rows[0][1] == "new", "and it says the file is not there yet"
    assert "other.wav" in [r[0] for r in rows], "the directory is still shown"

    # The cursor opens on it, which is what `here` means on the wire.
    marked = [l.split("\t")[1] for l in furniture(s).splitlines()
              if l.startswith("choice\t") and l.split("\t")[3] == "1"]
    assert marked == ["demo.wav"]

    # And typing narrows normally — the proposal is not in the way.
    act(s, "wants\texportWav\t0\toth")
    assert [r[0] for r in s.choices()] == ["other.wav"]


def test_a_plain_render_does_not_impose_a_length():
    """**The piece's own length, not a number this layer picked.**

    `audioperform` works the duration out of the score; passing one over
    the top of it made every render the same arbitrary size — a long
    piece cut short and a synth with no piece given seconds of tone that
    meant nothing.  A bar range is the one case where the caller knows
    better, because it said so.
    """
    from pathlib import Path

    import gestate.audioperform as ap
    from gestate.session import _export_wav

    seen = []

    def spy(argv):
        seen.append(list(argv))
        return 0

    was, ap.main = ap.main, spy
    try:
        _export_wav("sound : Sig Float\nsound = sine 220.0\n", Path("/tmp/x.wav"))
        assert "--seconds" not in seen[-1], \
            "a plain render imposed a length the score did not ask for"
        # And a bar range does say, because there it is the caller who knows.
        _export_wav("sound : Sig Float\nsound = sine 220.0\n",
                    Path("/tmp/x.wav"), span=(0.0, 4.0))
        assert seen[-1][seen[-1].index("--seconds") + 1] == "4.0"
    finally:
        ap.main = was


def test_overwrite_answers_only_a_question_that_was_asked():
    s = session()
    assert s.run("overwrite", "yes") == "nothing is waiting to be overwritten"


def test_an_export_of_nothing_is_a_refusal_not_a_build():
    """`clang` on an empty buffer is a long wait for an answer about a
    program that is not there."""
    s = session()
    assert s.run("exportClap", "") == "nothing to export yet"
    assert s.run("exportWav", "") == "nothing to export yet"


def test_performing_says_what_a_played_note_does():
    """**Not a mode of the editor.**  It changes what happens to a
    *note*, not what a *key* means — the letters go on typing.

    **Off to begin with**: a file is opened to be read at least as often
    as to be played, and three rows of keys taken from the document
    before anybody asked for them is a window that has decided what you
    are here for.
    """
    s = session()
    assert s.performing == "off", "no piano until one is asked for"
    assert s.run("pianoStep") == "notes sound and are written"
    assert s.performing == "step"
    assert s.run("pianoOff") == "notes go nowhere"
    assert s.run("pianoOn") == "notes sound"
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
    s.run("pianoOff")
    act(s, "note\t60\t1")
    assert played == [], "notes go nowhere"

    s.run("pianoOn")
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
        #: Where the caret is — `find` walks forward from it.
        self.pos = 0

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
    lines = [l.split("\t")[:3] for l in furniture(it).splitlines()
             if l.startswith("choice")]
    assert ["choice", "cutoff", "Chan Float"] in lines


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
    shown = len(it.commands())
    assert act(it, "filter\tloop") == f"3 of {shown}"
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


def test_every_shortcut_takes_control_except_tab():
    """There is one mode and you are typing in it, so a bare key is text.

    `play` was advertised as `Space` for a while, inherited from a window
    where the piano had the focus.  In an editor that is either a
    shortcut that never fires or an editor you cannot type a space into.

    **`Tab` is the one exemption, and it is the language that earns it.**
    A space is text in every line; a tab is not text here at all — the
    layout rule counts columns and a tab's width is the *renderer's*
    choice, so a tab-indented file means something other than it looks,
    and no `.ges` in the tree contains one.  So the key is spent on the
    question every other editor spends it on, and `keys.rs` no longer
    inserts one.

    The exemption is a *list*, checked exactly, so a second bare key
    cannot arrive by looking like the first.
    """
    bare = {name: key for name, key in KEYS.items()
            if not key.startswith("Ctrl-")}
    assert bare == {"fits": "Tab"}, \
        f"these could not work in a text editor: {bare}"


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
    # The exemption is advertised the same way, because the window looks
    # it up in the same table — a bare key that the list spelled
    # differently would be the eleven-advertised-two-implemented defect
    # with one entry instead of nine.
    assert advertised["fits"] == "Tab"


class _Showing:
    """A view port that can be pointed at either half."""

    def __init__(self):
        self.showing = "source"

    def show(self, what):
        self.showing = what
        return True

    def text(self):
        return ""


def test_canvas_answers_about_three_different_things():
    """A file that draws nothing, a canvas still compiling, and a window
    that cannot show one are three answers — and saying the first when
    the second is true sends somebody back to look for a bug in a
    program that is merely still building."""
    it = session()
    it.view = _Showing()
    it.bench.substrate = None
    it.bench.source = lambda: "sound : Sig Float\n"
    assert it.run("canvas") == "this file draws nothing"
    assert it.view.showing == "source", "and it does not switch to nothing"

    # Declared, not built yet — `start` compiles it on its own thread.
    it.bench.source = lambda: "substrate : Sig Sub\nsubstrate = moveXY 1 1\n"
    said = it.run("canvas")
    assert "will appear" in said, said
    assert it.view.showing == "canvas", "it opens and fills in"

    it.bench.substrate = object()
    assert it.run("canvas") == "canvas"


# ── Opening a file, and taking a name ────────────────────────────────────

def _looking(tmp_path):
    """A session whose file sits in a directory with a few others."""
    room = tmp_path / "here"
    room.mkdir()
    (room / "one.ges").write_text("sound : Sig Float\n")
    (room / "two.ges").write_text("sound : Sig Float\n")
    (room / "deeper").mkdir()
    it = session()
    it.bench.path = room / "one.ges"
    return it, room


def test_a_path_argument_offers_what_is_in_the_directory(tmp_path):
    it, _room = _looking(tmp_path)
    act(it, "wants\topen\t0\t")
    shown = [text for text, _note, _can, _step, _dim in it.choices()]
    assert shown[0] == "../", "going up is where the eye already is"
    assert "deeper/" in shown and "one.ges" in shown and "two.ges" in shown


def test_the_file_you_are_in_is_marked(tmp_path):
    it, _room = _looking(tmp_path)
    act(it, "wants\topen\t0\t")
    marked = [l.split("\t")[1] for l in furniture(it).splitlines()
              if l.startswith("choice") and l.split("\t")[3] == "1"]
    assert marked == ["one.ges"]


def test_going_up_stacks_rather_than_jumping(tmp_path):
    """**`..` is a path, not a word.**  Choosing it must leave a query
    you could have typed, because the query is what the next listing is
    read from — a row that put an absolute path there would end the walk
    you were in the middle of.

    The *row* stays `../`, which is what it means at every depth; the
    query it makes is what stacks.
    """
    it, _room = _looking(tmp_path)
    act(it, "wants\topen\t0\t")
    label, _note, _can, step, _dim = it.choices()[0]
    assert (label, step) == ("../", "../")

    act(it, "wants\topen\t0\t../")
    label, _note, _can, step, _dim = it.choices()[0]
    assert (label, step) == ("../", "../../"), "and again, and again"


def test_a_query_narrows_without_losing_the_way_up(tmp_path):
    it, _room = _looking(tmp_path)
    act(it, "wants\topen\t0\ttwo")
    assert [t for t, _n, _c, _s, _d in it.choices()] == ["two.ges"]


def test_opening_a_file_asks_the_window_for_it(tmp_path):
    it, room = _looking(tmp_path)
    win, _ed = a_window()
    it.view = win
    assert it.run("open", "two.ges") == "opened two.ges"
    assert win.wanted == str(room / "two.ges")
    assert "no file" in it.run("open", "nope.ges")


def test_steal_greys_what_is_taken_and_refuses_it(tmp_path):
    """The list is a courtesy; the check is the guarantee.  Overwriting
    is not something a name box should do by accident."""
    it, _room = _looking(tmp_path)
    act(it, "wants\tsteal\t0\t")
    rows = {text: can for text, _note, can, _step, _dim in it.choices()}
    assert rows["one.ges"] is False and rows["two.ges"] is False
    assert rows["deeper/"] is True, "a directory is a step, not a name"
    assert rows["../"] is True
    assert "is taken" in it.run("steal", "two.ges")


def test_steal_takes_a_free_name(tmp_path):
    it, room = _looking(tmp_path)
    win, _ed = a_window()
    it.view = win
    assert it.run("steal", "fresh.ges") == "writing fresh.ges from now on"
    assert it.bench.path == room / "fresh.ges"


def test_a_file_is_taken_from_where_the_list_walked_to(tmp_path):
    """**Relative to the query, not to the file you started in.**

    The list walks: after `../other/` a row says `x.ges` and means the
    one *there*.  Resolving against the open file's directory would find
    a different `x.ges`, or none — a walk that lied about where it had
    arrived.
    """
    it, room = _looking(tmp_path)
    (room / "deeper" / "two.ges").write_text("sound : Sig Float\n")
    win, _ed = a_window()
    it.view = win

    act(it, "wants\topen\t0\tdeeper/")
    assert [t for t, _n, _c, _s, _d in it.choices()] == ["../", "two.ges"]
    it.run("open", "two.ges")
    assert win.wanted == str(room / "deeper" / "two.ges"), \
        "the one in the directory the list had walked to"


def test_a_directory_is_a_step_and_a_file_is_the_answer(tmp_path):
    it, _room = _looking(tmp_path)
    act(it, "wants\topen\t0\t")
    rows = {text: step for text, _note, _can, step, _dim in it.choices()}
    assert rows["deeper/"] == "deeper/", "choosing it walks in"
    assert rows["../"] == "../"
    assert rows["one.ges"] == "", "a file ends the question"


def test_reopening_the_list_starts_where_the_file_is(tmp_path):
    """**Opening the list ends whatever it was asking.**

    `hide` clears every scrap of the last question and `show` cleared
    none of it on this side, so a list reopened after walking into a
    directory was handed that directory's rows — and `open` did not
    start where you are.
    """
    it, _room = _looking(tmp_path)
    act(it, "wants\topen\t0\t")
    home = [t for t, _n, _c, _s, _d in it.choices()]
    act(it, "wants\topen\t0\tdeeper/")
    assert [t for t, _n, _c, _s, _d in it.choices()] != home

    act(it, "asked")                       # what opening the list sends
    act(it, "filter\t")
    assert it.asking is None
    assert it.choices() == [], "nothing is being asked for"
    act(it, "wants\topen\t0\t")
    assert [t for t, _n, _c, _s, _d in it.choices()] == home
