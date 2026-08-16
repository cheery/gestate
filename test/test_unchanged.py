"""What an edit touched — `gestate/unchanged.py`.

A rebuild used to redo the file.  This decides which phases can keep
what they built, and the only interesting tests are the ones that say
**when it must not**: a wrong *yes* here is a stale score under a new
synth, which is silently the wrong music and the worst failure this
project can have.  So most of what is below is refusals.
"""

from __future__ import annotations

from gestate import unchanged

SYNTH = """\
# A little synth.
bassOsc : Float -> Sig Float
bassOsc hz = 0.6 * saw hz

bassVoice : Sig Gate -> Sig Key -> Sig Float
bassVoice g s = bassOsc (!hzOf s) * adsr env g

score : [: Void :]
score = tune >>= voices.bass

tune : [: Key :]
tune = '(Key 60 100) ++ '(Key 64 100)

bpm : Int
bpm = 96

sound : Sig Float
sound = 0.4 * bass
"""


def test_a_synth_constant_leaves_the_score_alone():
    """The case the whole thing is for: one number inside one voice."""
    after = SYNTH.replace("0.6 * saw", "0.61 * saw")
    assert unchanged.changed(SYNTH, after) == {"bassOsc"}
    assert unchanged.kept(SYNTH, after, ("score", "bpm"))


def test_a_note_does_not_leave_the_score_alone():
    """And the case it must never get wrong."""
    after = SYNTH.replace("Key 64 100", "Key 67 100")
    assert unchanged.changed(SYNTH, after) == {"tune"}
    assert not unchanged.kept(SYNTH, after, ("score", "bpm"))


def test_reaching_is_through_the_names_a_declaration_uses():
    """`score` names `tune`, so an edit to `tune` reaches it — the walk
    is transitive and over identifiers, which sees more than the real
    dependency graph and therefore skips less."""
    assert unchanged.reaches(SYNTH, ("score",)) >= {"score", "tune"}
    assert "bassOsc" not in unchanged.reaches(SYNTH, ("score", "bpm"))


def test_a_comment_between_declarations_costs_nothing():
    """Its own block, and comment blocks are not compared at all."""
    after = SYNTH.replace("# A little synth.", "# A little synth, tweaked.")
    assert unchanged.changed(SYNTH, after) == set()
    assert unchanged.kept(SYNTH, after)          # the strictest question


def test_a_comment_inside_a_body_is_a_change():
    """**Conservative on purpose.**  An indented comment is part of the
    block it sits in, and telling it from code would mean lexing — a
    string containing a `#` is enough to make that wrong, and being
    wrong here is the expensive direction."""
    after = SYNTH.replace("bassOsc hz = 0.6 * saw hz",
                          "bassOsc hz = 0.6 * saw hz  # louder")
    assert unchanged.changed(SYNTH, after) == {"bassOsc"}


def test_a_declaration_appearing_means_everything_moved():
    after = SYNTH + "\nextra : Int\nextra = 1\n"
    assert unchanged.changed(SYNTH, after) is None
    assert not unchanged.kept(SYNTH, after, ("score",))


def test_an_instance_is_never_reasoned_about():
    """An instance is chosen by *type*: nothing reaches it by name, so a
    changed one cannot be seen by a walk over identifiers.  It is
    structural, and any difference means everything moved."""
    before = SYNTH + "\ninstance FromMIDI Key where\n    noteOn c p v = Just (Key p v)\n"
    after = before.replace("Just (Key p v)", "Just (Key (p + 12) v)")
    assert unchanged.changed(before, after) is None


def test_a_bank_line_is_structural():
    """`voices bass 3 bassVoice` rewrites into a bank — a change to it
    changes channels, allocators and what the score is played by."""
    before = SYNTH + "\nvoices bass 3 bassVoice : Sig Float\n"
    after = before.replace("voices bass 3", "voices bass 4")
    assert unchanged.changed(before, after) is None


def test_the_editors_own_ask_lines_are_structural():
    """`canvas`, `notes` and `sink` are furniture rather than
    declarations, and a change to one is a change to what the window is
    being asked to build."""
    before = SYNTH + "\nnotes tune\n"
    after = before.replace("notes tune", "notes score")
    assert unchanged.changed(before, after) is None


def test_layout_is_meaning_and_is_not_normalised_away():
    """Two texts that differ only in indentation are two programs here,
    so nothing in this file trims whitespace."""
    after = SYNTH.replace("bassOsc hz = 0.6 * saw hz",
                          "bassOsc hz =\n    0.6 * saw hz")
    assert unchanged.changed(SYNTH, after) == {"bassOsc"}


def test_nothing_built_yet_is_a_rebuild():
    """`None` is not "nothing changed" — it is *ask me no more
    questions*, and every caller reads it as rebuild."""
    assert unchanged.changed(None, SYNTH) is None
    assert not unchanged.kept(None, SYNTH, ("score",))


def test_an_unroutable_edit_is_a_rebuild_rather_than_a_guess():
    """Half-typed text is the *normal* state of a file while somebody
    works, and it must answer rebuild rather than raise."""
    after = SYNTH.replace("bassOsc hz = 0.6 * saw hz", "bassOsc hz = 0.6 * saw (")
    assert unchanged.changed(SYNTH, after) == {"bassOsc"}
    assert unchanged.kept(SYNTH, after, ("score", "bpm"))
    broken = "voices\n  ??? not a program at all"
    assert unchanged.changed(SYNTH, broken) is None


def test_with_no_roots_the_question_is_the_strictest_one():
    """What a phase asks when its dependencies cannot be bounded."""
    after = SYNTH.replace("0.6 * saw", "0.61 * saw")
    assert unchanged.kept(SYNTH, after, ("score", "bpm"))
    assert not unchanged.kept(SYNTH, after)


def test_an_operator_declaration_is_named_by_its_operator():
    before = SYNTH + "\n(|+|) : Int -> Int -> Int\n(|+|) a b = a + b\n"
    after = before.replace("(|+|) a b = a + b", "(|+|) a b = a + b + 1")
    assert unchanged.changed(before, after) == {"(|+|)"}


BOXED = """\
tune : [: Int :]
tune = '60 ++ '63 ++ '53 ++ '56

notes tune

score : [: Void :]
score = do
    x <- tune
    voices.lead (Key x 100)

sound : Sig Float
sound = lead * 0.3
"""


def test_a_score_box_is_drawn_from_what_its_ask_names():
    """**A phase's roots are what it reads, not what it is called.**

    Henri's `untitled.ges` has no `substrate` in it at all, only a
    `notes tune` ask.  Asking whether anything reachable from
    `substrate` had moved is asking about an empty set, so every edit
    "kept" the pictures — and the score box went on describing the text
    as it was before the drag that had just rewritten it.  Found within
    the hour of the skipping being built, by a hand dragging four notes
    in a row.

    What saved it from being a wrong note rather than a refusal is the
    box's own guard: *the file has moved under the picture*.
    """
    assert unchanged.picture_roots(BOXED) == ("substrate", "tune")
    after = BOXED.replace("'60 ++ '63", "'58 ++ '63")
    assert unchanged.changed(BOXED, after) == {"tune"}
    assert not unchanged.kept(BOXED, after, unchanged.picture_roots(BOXED))


def test_a_synth_edit_still_leaves_the_boxes_alone():
    """The win is kept: a roll of `tune` does not care what `sound`
    multiplies by."""
    after = BOXED.replace("lead * 0.3", "lead * 0.35")
    assert unchanged.changed(BOXED, after) == {"sound"}
    assert unchanged.kept(BOXED, after, unchanged.picture_roots(BOXED))


def test_the_substrate_is_still_a_root():
    """A file that *does* declare one keeps the original question."""
    drawn = "substrate : Sig Sub\nsubstrate = disc peak\n\npeak : Sig Float\npeak = 0.5\n"
    assert unchanged.picture_roots(drawn) == ("substrate",)
    after = drawn.replace("peak = 0.5", "peak = 0.6")
    assert not unchanged.kept(drawn, after, unchanged.picture_roots(drawn))
