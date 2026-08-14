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

import time

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

    def touch(self, kind, x, y):
        self.log.append(("touch", kind, x, y))

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


def test_a_written_transcript_closes_its_dialog(tmp_path):
    """The same say-when-you-are-done `open`, `template` and `symbol`
    use: Return on a finished transcript meant *write it again*, and
    the keystrokes after saving a recording are aimed at the work."""
    it, room = _looking(tmp_path)
    win, ed = a_window()
    it.view = win
    it.run("play")                       # something to record
    said = it.run("transcript", str(room / "t-session.ges"))
    assert said.startswith("wrote t-session.ges")
    assert "close" in ed.orders


def test_bars_count_from_zero_like_everything_else():
    """**One house style, kept in the window too.**

    Bars used to count from one — what a score on paper does, and
    defensible in a tool for players.  It is wrong in this one: gestate
    counts ticks, samples, voices and list indices from zero, and an
    interface that alone said *bar 1* for the first bar made the reader
    do arithmetic to cross between the program and the window.

    Lines stay 1-based and that is not an inconsistency: those are a
    *text* coordinate, every editor and every compiler message counts
    them from one, and matching the outside world matters more there.
    """
    s = session()
    s.run("seek", 0)
    s.run("loop", 2, 4)
    assert s.bench.log == [("seek", 0.0), ("loop", 8.0, 16.0)]
    assert s.run("seek", 1) == "at bar 1"
    assert s.bench.log[-1] == ("seek", 4.0), "bar 1 is the second bar"


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
    assert s.run("canvas") == ("this file draws nothing — a canvas is a "
            "`substrate : Sig Sub` declaration")


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
              "Answer": "no",
              # A port this machine certainly does not have, so `midiOn`
              # answers about the name rather than opening anything.
              "Device": "no-such-controller",
              # A letter that reaches the first cell of the symbol table.
              "Symbol": "a"}
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


def test_the_completion_does_not_offer_what_a_program_cannot_say():
    """`constSig` is `!`'s own node and naming it is refused
    (`internals.RENDERER_PRIVATE`) — a completion offering it is the
    list teaching a word the compiler then takes back.  Asked in full
    it still answers, because *what is this thing my editor showed me*
    stays a fair question about machinery.
    """
    s = session()
    offered = {row[0] for row in s.names("everything")}
    assert "constSig" not in offered
    assert "constSig : a -> Sig a" in s.run("what", "constSig")


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


def test_a_letter_reaches_exactly_one_symbol():
    """**One cell, one keystroke** — which is the whole of the grid.

    Matching names as well as letters made `a` also match `backslash`,
    `bar` and half the table, so the one keystroke the table exists to
    make sufficient was not.
    """
    from gestate.session import SYMBOLS, _letter

    glyphs = [g for g, _n in SYMBOLS]
    assert len(set(glyphs)) == len(glyphs), "the same symbol twice"
    labels = [_letter(i) for i in range(len(SYMBOLS))]
    assert len(set(labels)) == len(labels), "two cells with one label"
    s = session()
    # **A label is a prefix, so a query narrows rather than picks.**  `a`
    # is also the start of `aa`, and returning only the exact match put
    # every cell past `z` out of reach by name — so the row is kept and
    # the exact one is first, where the cursor already is.
    s.asking = ("symbol", 0, "a")
    rows = s.choices()
    assert rows[0] == ("a", ">"), "one keystroke and Return missed"
    assert all(l.startswith("a") for l, _g in rows)
    # And one more letter reaches past `z`.
    s.asking = ("symbol", 0, "aa")
    assert s.choices() == [("aa", "||")]
    # The symbol itself and its name still reach it, for somebody who
    # knows what they want and will not count to `i`.
    s.asking = ("symbol", 0, "`")
    assert s.choices() == [("i", "`")]
    s.asking = ("symbol", 0, "join")
    assert s.choices() == [("ad", "\\/")]
    s.asking = ("symbol", 0, "lambda")
    assert s.choices() == [("t", "=>")]


def test_a_symbol_goes_in_and_the_table_goes_away():
    """Typing a character is finished when it is typed.  Return on a
    finished call means *again*, which left the table sitting over the
    line you had just changed — hiding the one thing you opened it to
    see."""
    view = _Inserting()
    view.closed = False
    view.close_list = lambda: setattr(view, "closed", True) or True
    s = session(view=view)
    assert s.run("symbol", "a") == "typed >"
    assert view.put == [">"]
    assert view.closed, "the table stayed up"
    # The symbol itself works as an argument too — a command is a thing
    # you can type, and `symbol >` refusing while `symbol a` worked
    # would be a picker that only answers to its own table.
    assert s.run("symbol", "=>") == "typed =>"
    assert s.run("symbol", "nope") == "no symbol `nope`"


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
        #: The window keeps the saved root and volunteers this; the
        #: model only ever mirrors it.
        self.saved = True

    def note_state(self, zoom, rungs, undos, redos, saved=True,
                   top=0, rows=40, sel=False, clip=False):
        self.saved = saved
        self.top, self.rows = top, rows
        self.sel, self.clip = sel, clip

    def mark_saved(self):
        self.saved = True
        return True

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


class _WithMidi:
    """A workbench with controllers plugged in, and one of them open."""

    def __init__(self, ports=("Launchkey", "nanoKONTROL"), open_at=None):
        self.ports = list(ports)
        self.opened = open_at
        self.log = []
        self.values, self.ranges = {}, {}
        self.sites, self.banks, self.knob_types, self.holes = [], [], {}, []

    def midi_ports(self):
        return list(self.ports)

    @property
    def midi_port(self):
        return self.opened

    def midi_open(self, port=None):
        self.opened = port or (self.ports[0] if self.ports else None)
        self.log.append(("open", port))
        return self.opened is not None

    def midi_close(self):
        if self.opened is None:
            return False
        self.log.append(("close", self.opened))
        self.opened = None
        return True

    def source(self):
        return ""


def test_the_device_list_says_which_one_is_listening():
    """**Choosing a device and seeing which is live are one act.**

    They are the same question asked half a second apart, and a window
    that could only tell you afterwards is how an evening goes into
    deciding whether the keyboard is broken.
    """
    s = Session(bench=_WithMidi(open_at="nanoKONTROL"))
    s.asking = ("midiOn", 0, "")
    assert s.choices() == [("Launchkey", "idle"),
                           ("nanoKONTROL", "listening")]
    # The cursor opens on the live one, which is what `here` means.
    marked = [l.split("\t")[1] for l in furniture(s).splitlines()
              if l.startswith("choice\t") and l.split("\t")[3] == "1"]
    assert marked == ["nanoKONTROL"]
    # And typing narrows it like any other list.
    s.asking = ("midiOn", 0, "launch")
    assert [n for n, _note in s.choices()] == ["Launchkey"]


def test_midiOn_tells_three_different_facts_apart():
    """A machine with no MIDI, a name that is not one of them, and a port
    that refused are not the same thing — `canvas`'s lesson, again."""
    none = Session(bench=_WithMidi(ports=()))
    assert none.run("midiOn", "") == "no MIDI input on this machine"

    s = Session(bench=_WithMidi())
    assert s.run("midiOn", "nope") == "no MIDI input `nope`"
    assert s.run("midiOn", "Launchkey") == "listening to Launchkey"
    # No name means the first there is.
    s2 = Session(bench=_WithMidi())
    assert s2.run("midiOn", "") == "listening to Launchkey"


def test_opening_a_second_device_closes_the_first():
    """Two listeners on one machine is two copies of every note, and
    picking from a list is a change of device far more often than a
    first one."""
    bench = _WithMidi(open_at="Launchkey")
    s = Session(bench=bench)
    assert s.run("midiOn", "nanoKONTROL") == "listening to nanoKONTROL"
    assert bench.midi_port == "nanoKONTROL"


def test_midiOff_says_when_there_was_nothing_to_stop():
    bench = _WithMidi(open_at="Launchkey")
    s = Session(bench=bench)
    assert s.run("midiOff") == "stopped listening to Launchkey"
    assert bench.midi_port is None
    assert s.run("midiOff") == "not listening to any controller"


def test_a_knob_the_sound_never_reaches_is_drawn_and_marked():
    """**A knob with no site is not a knob that does not exist.**

    `audiospans` reports control sources found *in the graph*, so a
    `mkKnob` nothing downstream of `sound` reads has none — and the
    margin drew nothing at all, which reads as the editor having missed
    the line rather than as the program having ignored it.  Declaring a
    parameter and forgetting to use it is an ordinary mistake, and the
    window is best placed to point at it.
    """
    s = session()
    s.bench.sites = [_Site("cutoff", 2)]
    s.bench.loose = [("spare", 5, "0.7", True), ("steps", 9, "40", False)]
    rows = [l for l in furniture(s).splitlines() if l.startswith("knob\t")]
    assert rows == ["knob\tcutoff\t2\t40\t0\t100\tInt\t1",
                    "knob\tspare\t5\t0.7\t0.0\t1.0\tFloat\t0",
                    "knob\tsteps\t9\t40\t0\t100\tInt\t0"]


def test_a_wired_knob_is_never_listed_twice():
    """The scan reads the text and the sites read the graph, so a name in
    both must come through once — as the connected one."""
    s = session()
    s.bench.sites = [_Site("cutoff", 2)]
    s.bench.loose = [("cutoff", 2, "0.4", True)]
    rows = [l for l in furniture(s).splitlines() if l.startswith("knob\t")]
    assert len(rows) == 1 and rows[0].endswith("\t1")


def test_colouring_uses_the_compilers_own_tokenizer():
    """**One lexer, one truth.**

    A second lexer in the window would be fast and would be a second
    front end that could disagree with the compiler — the root cause
    `spec/comments.md` is written about.  So a colour is the tokenizer's
    own opinion or it is not shown.
    """
    from gestate.session import painted

    assert painted("cutoff = mkKnob 0.4  # a comment") == \
        "7:1:op 16:3:num 21:11:note"
    # A name gets no run and falls through to the ordinary ink — the
    # table says what is worth colouring, not what exists.
    assert "mkKnob" not in painted("x = mkKnob 1.0")


def test_a_file_that_does_not_compile_still_colours():
    """**The lexer is total, which is what the spec's blocker missed.**

    `spec/workbench.md` deferred colouring because it "needs the parser
    to survive a broken file".  It needs the *lexer*, and that already
    does: half a line colours as far as it goes.
    """
    from gestate.session import painted

    for broken in ("sound = ((", 'x = "unterminated', "f x = ) ) )"):
        painted(broken)                      # the point is it returns
    assert painted("sound = ((").startswith("6:1:op")


def test_only_the_visible_lines_are_painted():
    """Colouring a million-line file to draw fifty rows would make the
    rope decorative, which is the argument `view.rs` opens with."""
    view = _Editing("")
    view.visible = lambda: [(3, "x = 1"), (4, "y = Adsr 2")]
    s = session(view=view)
    rows = [l for l in furniture(s).splitlines() if l.startswith("paint\t")]
    assert [r.split("\t")[1] for r in rows] == ["3", "4"]
    assert "con" in rows[1], "a constructor was not coloured"


def test_an_inert_file_takes_the_syntax_off_and_loses_the_transport():
    """A `.txt` is prose: colouring it with the program's lexer would
    be wrong twice over, and a stopped transport for a file that cannot
    play reads as something waiting to be fixed.  The description says
    `inert` instead, and the window wears `[inert]` in its place."""
    view = _Editing("")
    view.visible = lambda: [(1, "y = Adsr 2")]
    s = session(view=view)
    s.bench.inert = True
    said = furniture(s).splitlines()
    assert "inert\t1" in said
    assert not [l for l in said if l.startswith("paint\t")], \
        "prose was coloured as a program"
    assert not [l for l in said if l.startswith("play\t")], \
        "an inert file grew a transport"

    # And `apply` answers with the act that happens — a save, with no
    # rebuild coming that "applying" would promise — while `play` says
    # why nothing will, instead of a "stopped" that reads as breakage.
    assert s.run("apply") == "saving"
    assert s.run("play") == "nothing plays — the file is inert"


def test_the_status_line_says_the_file_and_whether_it_is_written():
    """**An edit you have not saved looked exactly like one you had.**

    In a window whose whole premise is that saving is what you press to
    hear the change, that is the one fact the chrome could not say.  `[+]`
    is what every editor with a modified flag uses, so it needs no
    explaining.

    Two events rather than a comparison: `view.text() != bench.source()`
    is a whole-document copy and a file read, on a description derived
    every two milliseconds.
    """
    view = _Editing("x = 1\n")
    s = session(view=view)
    s.bench.path = "demo.ges"

    def row():
        return next(l for l in furniture(s).splitlines()
                    if l.startswith("file\t"))

    assert row() == "file\tdemo.ges\t0"
    act(s, "state\t0\t1\t1\t0\t0")           # the window: not saved
    assert row() == "file\tdemo.ges\t1", "an edit did not mark it"
    s.run("apply")
    assert row() == "file\tdemo.ges\t0", "saving did not clear it"
    # **And undoing back to the saved text clears it too**, which is the
    # whole reason this is the window's comparison rather than a flag:
    # moving twice and arriving back is not modified.
    act(s, "state\t0\t1\t2\t0\t0")
    assert row() == "file\tdemo.ges\t1"
    act(s, "state\t0\t1\t1\t1\t1")           # undone, and equal again
    assert row() == "file\tdemo.ges\t0", "undo to saved still showed [+]"


def test_auditioning_leaves_the_file_unsaved():
    """`audition` changes the sound and not the file, which is what it is
    for — so the marker has to stay up."""
    view = _Editing("x = 1\n")
    s = session(view=view)
    s.bench.path = "demo.ges"
    act(s, "state\t0\t1\t1\t0\t0")
    s.run("audition")
    assert "file\tdemo.ges\t1" in furniture(s), "audition cleared the mark"


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
    assert "knob\tcutoff\t40\t40\t0\t100\tInt\t1" in lines
    assert "knob\tdrive\t44\t0.5\t0.0\t1.0\tFloat\t1" in lines
    assert any(line.startswith("play\t") for line in lines)
    # And every command, so the palette has something to show.
    assert sum(1 for line in lines if line.startswith("command\t")) == \
        len(s.commands())


def test_a_many_line_trouble_is_many_rows_with_one_line_number():
    """The complaint crosses whole, one `trouble` row per line — the
    content box under the line draws all of it, and a box one line deep
    proves nothing (`spec/workbench.md` §"Content boxes" B1).  Tabs
    become spaces because the wire's fields are tab-separated, and an
    old window reading only the first row draws what it always drew."""
    from gestate.session import furniture

    s = session()
    s.bench.trouble = ("expected a type, got `sound` (at 12:8-12:11)\n"
                       "because `sound`\tis a signal\n"
                       "and a signal is not a type")
    rows = [l for l in furniture(s).splitlines()
            if l.startswith("trouble\t")]
    assert rows == [
        "trouble\t12\texpected a type, got `sound` (at 12:8-12:11)",
        "trouble\t12\tbecause `sound`    is a signal",
        "trouble\t12\tand a signal is not a type",
    ]


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


def test_a_touch_is_a_verb_like_any_other():
    """The canvas is an input device, and this seam is where it was lost.

    The wiring from the window to `Workbench.touch` had exactly one
    implementation and exactly one test, both in the pygame editor, and
    both were deleted in the same commit — so the suite stayed green for
    a day while every fader in `examples/audio` was dead (fixme.md F101).
    This test is at the *verb protocol*, which is the boundary contract,
    so it survives any rewrite of the view.  What a touch does to a real
    substrate is `test_audioeditor.py`'s half.
    """
    from gestate.session import act

    s = session()
    assert act(s, "touch\tpress\t150\t60") == ""
    assert act(s, "touch\tdrag\t150\t90") == ""
    assert act(s, "touch\trelease\t150\t90") == ""
    assert s.bench.log == [("touch", "press", 150, 60),
                           ("touch", "drag", 150, 90),
                           ("touch", "release", 150, 90)]
    # The refusal is a sentence, like every refusal on this wire.
    assert act(s, "touch\tpress\there\tnow") == \
        "touch: `here now` is not a place"


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


def test_a_listened_banks_score_lines_are_layered_away():
    """The score's word: a bank whose switch is on is MIDI's — `listen`
    says "the score no longer drives it" — so every score line writing
    `voices.<bank>` crosses as an `away` row, and only then: a bank the
    score drives, or one not scored at all, floats nothing."""
    s = session()
    s.bench.banks = [{"name": "lead", "count": 4, "line": 9,
                      "channels": [], "wired": True,
                      "mentions": [12, 20]}]
    s.bench.scored_banks = lambda: {"lead"}
    s.bench.takes_midi = lambda name: True
    listening = {"lead": False}
    s.bench.listening = lambda name: listening[name]
    rows = [l for l in furniture(s).splitlines() if l.startswith("away")]
    assert rows == [], "the score drives it; nothing floats"
    listening["lead"] = True
    rows = [l for l in furniture(s).splitlines() if l.startswith("away")]
    assert rows == ["away\t12\taway", "away\t20\taway"]
    # A disconnected bank says so at the same lines, and the word wins
    # over "away": silent is silent, whatever MIDI holds.
    s.bench.banks[0]["wired"] = False
    rows = [l for l in furniture(s).splitlines() if l.startswith("away")]
    assert rows == ["away\t12\tdisconnected", "away\t20\tdisconnected"]
    # And throwing the switch on a disconnected bank is allowed but the
    # sentence must not promise sound (lol-session.ges: keys played
    # into silence with the switch proudly on).
    def listen(name, on):
        listening[name] = on
    s.bench.listen = listen
    assert s.run("listen", "lead") == \
        "lead hears the keyboard — though it is disconnected"


def test_copy_and_paste_answer_from_the_mirror():
    """fixme.md F114: the chords worked and the palette could not teach
    them.  As commands they answer from the state mirror the way `undo`
    does — "copied" over nothing selected is a sentence that lies."""
    s = session()
    win, ed = a_window()
    s.view = win
    win.note_state(0, 3, 0, 0, True, 0, 40, sel=False, clip=False)
    assert s.run("copy") == "nothing selected"
    assert s.run("cut") == "nothing selected"
    assert s.run("paste") == "nothing to paste"
    assert ed.orders == [], "a refusal orders nothing"
    win.note_state(0, 3, 0, 0, True, 0, 40, sel=True, clip=True)
    assert s.run("copy") == "copied"
    assert s.run("cut") == "cut"
    assert s.run("paste") == "pasted"
    assert ed.orders == ["copy", "cut", "paste"]


def test_the_state_gesture_carries_selection_and_clipboard():
    """Fields eight and nine — and a window built before them still
    reports the seven it has rather than being dropped for the two it
    does not."""
    s = session()
    win, _ed = a_window()
    s.view = win
    act(s, "state\t0\t3\t0\t0\t1\t0\t40\t1\t1")
    assert win.sel and win.clip
    act(s, "state\t0\t3\t0\t0\t1\t0\t40")
    assert not win.sel and not win.clip


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
    assert act(it, "wants\tset\t0\t") == "2 name(s)"
    assert [r[0] for r in it.choices()] == ["cutoff", "pitch"]
    lines = [l.split("\t")[:3] for l in furniture(it).splitlines()
             if l.startswith("choice")]
    assert ["choice", "cutoff", "Chan Float"] in lines


def test_not_every_named_is_the_same_question():
    """**Offering a choice that cannot work is a list telling you a lie.**

    `set cutoff` only means anything for a knob and `listen` only for a
    bank; every `Named` argument used to be handed the same pair of
    lists, so `listen` offered knobs it would have to refuse.
    """
    it = session()
    it.bench.sites = (_Site("cutoff", 12),)
    it.bench.knob_types = {"cutoff": "Float"}
    it.bench.banks = [{"name": "lead", "line": 4, "count": 4}]

    it.asking = ("set", 0, "")
    assert [r[0] for r in it.choices()] == ["cutoff"]
    it.asking = ("listen", 0, "")
    assert [r[0] for r in it.choices()] == ["lead"]


def test_what_completes_over_everything_there_is():
    """**`what` already answered out of the reference; now it offers it.**

    It reaches the language's own documentation when a name is not in
    the file, so a completion that offered only the file's names was
    offering less than the command could do.

    Grouped, and the group is the note: what is in the window first,
    then the libraries, each tagged with which one it is in — that order
    answers *what did I call it*, which is the question somebody has
    when they open the list.
    """
    it = session()
    it.bench.sites = (_Site("cutoff", 12),)
    it.bench.knob_types = {"cutoff": "Float"}
    it.asking = ("what", 0, "")
    rows = it.choices()
    names = [r[0] for r in rows]
    assert names[0] == "cutoff", "the window's own names do not come first"
    assert "adsr" in names, "a library name is not offered"
    assert len(names) > 100, f"only {len(names)} names offered"
    # The note says which library, so the list reads as groups.
    note = {r[0]: r[1] for r in rows}["adsr"]
    assert note and note != "declared here", f"adsr is tagged {note!r}"
    # And it filters like every other list.
    it.asking = ("what", 0, "lowpass")
    assert all("lowpass" in n.lower() for n, _note, _kind in it.choices())


def test_the_builtin_types_are_offered_too():
    """**`Int` and `Bool` are in no `.ges` file.**

    They are the compiler's own, so the reference — generated from the
    libraries' prose — has never heard of them, and a completion over
    "everything" that could not offer `Int` was offering everything
    except the words a beginner reaches for first.

    Read from `kindcheck`'s own table, so a type the compiler learns is
    a type this offers.  The internal spellings stay out: `Tuple2` is
    what a pair is called inside the checker and `(a, b)` is what
    anybody writes.
    """
    it = session()
    for want in ("Int", "Bool", "Float", "Sig", "List"):
        it.asking = ("what", 0, want)
        rows = it.choices()
        assert rows and rows[0][0] == want, f"{want}: {rows[:2]}"
        assert rows[0][2] == "type", f"{want} is not offered as a type"
    it.asking = ("what", 0, "Tuple")
    assert not [n for n, _x, _y in it.choices() if n.startswith("Tuple")], \
        "the checker's internal spelling for a pair was offered"


def test_what_answers_about_a_builtin_it_offered():
    """**Offering a choice and then refusing it is the shape to avoid.**

    `Int` was in the list and answered `no declaration` when picked.
    The kind is what there is to say — `Int` is a type, `Sig` is a type
    constructor — and knowing which is what the reader wanted.
    """
    s = session(view=_Editing(""))
    assert s.run("what", "Int") == "Int : Type — built in"
    assert s.run("what", "Sig") == "Sig : (Type -> Type) — built in"
    assert s.run("what", "nobody") == "no declaration `nobody`"


def test_a_type_is_marked_as_one_on_the_wire():
    """A type is a different sort of answer from a function — you reach
    for one to say what something *is* and the other to say what it
    *does* — so the row carries which, and the window tints it."""
    it = session()
    it.asking = ("what", 0, "Adsr")
    rows = [l.split("\t") for l in furniture(it).splitlines()
            if l.startswith("choice\t")]
    by = {r[1]: r[-1] for r in rows}
    assert by.get("Adsr") == "type"
    assert by.get("adsr") == "value", "a function was marked a type"


def test_names_are_ranked_the_way_commands_are():
    it = session()
    it.bench.sites = (_Site("cut", 1), _Site("cutoff", 2), _Site("uncut", 3))
    it.bench.knob_types = {}
    assert [r[0] for r in it.naming("cut")] == ["cut", "cutoff", "uncut"]


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
    assert it.run("canvas") == ("this file draws nothing — a canvas is a "
            "`substrate : Sig Sub` declaration")
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
    it, room = _looking(tmp_path)
    act(it, "wants\topen\t0\t")
    shown = [text for text, _note, _can, _step, _dim in it.choices()]
    assert shown[0] == "../", "going up is where the eye already is"
    # **The note says where you are, not where up goes** — the parent's
    # absolute path read as a destination, when the row means a step.
    notes = {t: n for t, n, *_ in it.choices()}
    assert notes["../"].startswith("you are here: ")
    assert notes["../"].endswith(str(room)), notes["../"]
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


def test_a_file_that_arrives_shows_up_without_touching_the_query(tmp_path):
    """**The first bug a user of this editor reported.**

    `choices` is answered once per *question* — the poll comes round
    every few milliseconds and re-ranking `what`'s five hundred names on
    each one would eat the frame.  But two of the answers are not about
    the program at all: a `Path` question lists a directory, and the
    directory can change while the query sits untouched.  So a dialog
    left open showed a listing from whenever it opened, and a file moved
    in never appeared — not late, *never*, because nothing but a
    keystroke could re-key the cache.

    It hid because reproducing it means leaving the query alone.  Anyone
    checking by typing part of the new file's name changes the key,
    which re-lists, which shows the file.
    """
    it, room = _looking(tmp_path)
    act(it, "wants\topen\t0\t")
    assert "three.ges" not in [t for t, *_ in it.choices()]

    (room / "three.ges").write_text("sound : Sig Float\n")
    time.sleep(Session.OUTSIDE_EVERY * 1.5)

    assert "three.ges" in [t for t, *_ in it.choices()], \
        "the directory changed and the question did not"


def test_a_listing_is_not_re_read_on_every_poll(tmp_path):
    """**And the reason the cache exists is still honoured.**

    The fix must not turn a redraw back into a directory walk: the poll
    is 2ms after a keystroke, and `furniture` reads this.  Between looks
    the answer stands, which is what `OUTSIDE_EVERY` buys.
    """
    it, room = _looking(tmp_path)
    act(it, "wants\topen\t0\t")
    first = it.choices()

    (room / "four.ges").write_text("sound : Sig Float\n")
    # No sleep: the throttle has not elapsed, so this is the cached
    # answer and it is the *same object*, not an equal one.
    assert it.choices() is first


def test_the_cache_still_watches_the_directory_the_walk_reached(tmp_path):
    """`_directory` is shared with `_listing` so the two cannot drift.

    A key that statted the file's own folder while the list showed
    `deeper/` would be a cache watching the wrong place — the staleness
    bug again, wearing the fix's clothes.
    """
    it, room = _looking(tmp_path)
    act(it, "wants\topen\t0\tdeeper/")
    assert [t for t, *_ in it.choices()] == ["../"], "empty but for the way up"

    (room / "deeper" / "inner.ges").write_text("sound : Sig Float\n")
    time.sleep(Session.OUTSIDE_EVERY * 1.5)

    assert "inner.ges" in [t for t, *_ in it.choices()]


def test_a_query_narrows_without_losing_the_way_up(tmp_path):
    it, _room = _looking(tmp_path)
    act(it, "wants\topen\t0\ttwo")
    assert [t for t, _n, _c, _s, _d in it.choices()] == ["two.ges"]


def test_opening_a_file_asks_the_window_for_it(tmp_path):
    it, room = _looking(tmp_path)
    win, ed = a_window()
    it.view = win
    assert it.run("open", "two.ges") == "opened two.ges"
    assert win.wanted == str(room / "two.ges")
    # **And the list goes away**: Return on a finished call means
    # *again*, which is meaningless for `open` — the table sat over the
    # freshly opened file and caught the first keystrokes somebody
    # aimed at their code.  The next key types into the file.
    assert "close" in ed.orders


def test_open_warns_and_then_lets_the_choice_stand(tmp_path):
    """F113's companion: unsaved changes **warn, they do not gate**.
    The warning fires when `open` is picked and the window holds it up
    for as long as the question is open — and a person who chooses a
    file past it has decided, so the switch proceeds.  They got their
    warning."""
    it, room = _looking(tmp_path)
    win, ed = a_window()
    it.view = win
    win.note_state(zoom=0, rungs=3, undos=1, redos=0, saved=False)
    act(it, "wants\topen\t0\t")
    assert "warn\twarning: unsaved changes" in ed.orders
    assert it.run("open", "two.ges") == "opened two.ges", \
        "warned is not forbidden"
    assert win.wanted == str(room / "two.ges")


def test_picking_open_says_unsaved_at_once(tmp_path):
    """The courtesy half: with unsaved changes the eventual choice will
    be refused, and learning that after walking three directories is
    the refusal arriving late — so the warning fires the moment `open`
    is picked.  Once: every keystroke in the box re-asks, and a warning
    per letter is a warning nobody reads."""
    it, _room = _looking(tmp_path)
    win, ed = a_window()
    it.view = win
    win.note_state(zoom=0, rungs=3, undos=1, redos=0, saved=False)
    act(it, "wants\topen\t0\t")
    assert ed.orders.count("warn\twarning: unsaved changes") == 1
    act(it, "wants\topen\t0\ttw")
    assert ed.orders.count("warn\twarning: unsaved changes") == 1, \
        "typing in the box must not repeat the warning"
    # And a saved file picks open without a word.
    win.note_state(zoom=0, rungs=3, undos=1, redos=0, saved=True)
    ed.orders.clear()
    act(it, "wants\topen\t0\t")
    assert not any(o.startswith("warn") for o in ed.orders)


def test_a_typed_path_is_not_walked_twice(tmp_path):
    """fixme.md F122, from Henri's transcript: `transcript
    ../../x.ges` typed into a box whose question had walked to
    `examples/audio/` resolved the `../..` twice and landed in
    `/home/`.  A picked row is bare and needs the walk; a typed query
    is whole and must not get it."""
    it, room = _looking(tmp_path)
    deeper = room / "deeper"
    it.bench.path = deeper / "d.ges"
    # The question has walked nowhere; the typed answer carries its
    # own way up.
    it.asking = ("transcript", 0, "../up.ges")
    assert it._where("../up.ges") == (room / "up.ges").resolve()
    # A picked row is still resolved against the walk.
    it.asking = ("open", 0, "../")
    assert it._where("one.ges") == (room / "one.ges").resolve()


def test_opening_a_file_that_is_not_text_is_a_sentence(tmp_path):
    """A `.wav` used to quit the whole editor: the switch read the
    bytes in the gesture loop and the decode raised.  Refused here,
    with the file named and the reason said."""
    it, room = _looking(tmp_path)
    (room / "take.wav").write_bytes(bytes(range(256)) * 8)
    win, _ed = a_window()
    it.view = win
    assert it.run("open", "take.wav") == \
        "cannot open take.wav: not a text file"
    assert win.wanted is None
    # **Where the decode fails is the whole test.**  A multibyte
    # character straddling the sniff's chunk edge is the chunk's
    # fault, not the file's — the first cut refused `duet.ges` itself,
    # whose box-drawing headers put a `─` on exactly the boundary.
    edge = ("x" * 4094 + "─" + "plenty of honest text after the edge\n")
    (room / "edge.ges").write_text(edge)
    assert it.run("open", "edge.ges") == "opened edge.ges"
    from pathlib import Path as _P

    duet = (_P(__file__).resolve().parent.parent
            / "examples" / "audio" / "duet.ges")
    it.asking = None
    assert it.run("open", str(duet)) == "opened duet.ges", \
        "the flagship example must open"


def test_opening_a_name_nobody_has_used_starts_a_fresh_file(tmp_path):
    """`open notpresent.ges` used to answer `no file` — but a name
    nobody has used is a file being started, and the workbench has
    known that shape since the starter text: a `Workbench` on a missing
    path opens with `STARTER` and the first save creates the file.  The
    sentence says which of the two happened, so a typo of an existing
    name is at least visible as a fresh file."""
    it, room = _looking(tmp_path)
    win, _ed = a_window()
    it.view = win
    assert it.run("open", "nope.ges") == "new file nope.ges — saving creates it"
    assert win.wanted == str(room / "nope.ges")
    assert not (room / "nope.ges").exists(), "opening must not touch disk"
    # A started file is text — a name wearing a binary suffix is a
    # miss, not a request: `open blip.wav` against the wrong directory
    # used to start a STARTER synth *named* blip.wav, sine and all
    # (F120's second face).  Anything honestly textual still starts.
    win.wanted = None
    assert it.run("open", "blip.wav") == \
        "no file blip.wav — and a new .wav would not be text"
    assert win.wanted is None
    assert it.run("open", "notes.txt") == \
        "new file notes.txt — saving creates it"
    assert win.wanted == str(room / "notes.txt")


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


def test_a_touched_channel_is_the_meaning_not_the_place():
    """`spec/workbench.md` §"The canvas walks over crust": a window
    that walks the substrate hit-tests and clamps where the picture
    is, so what crosses is the channel's name and the fraction its
    element produced — never coordinates."""
    s = session()
    s.bench.touched = lambda name, v: s.bench.log.append(("touched", name, v))
    assert act(s, "touched\twarmthChan\t0.62") == ""
    assert s.bench.log[-1] == ("touched", "warmthChan", 0.62)
    # A value that is not one is a sentence, not a traceback.
    assert act(s, "touched\twarmthChan\tup-a-bit").startswith("touched:")
    # And a bench from before the verb existed loses a drag, not the
    # editor — the same lenience every gesture keeps.
    del s.bench.touched
    assert act(s, "touched\twarmthChan\t0.5") == ""
