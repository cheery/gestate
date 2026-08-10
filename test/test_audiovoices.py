"""`voices` — a bank of N copies of one voice.

    voices lead 8 plucked : Sig Float

Polyphony is the one thing the static fragment cannot express: allocating a
voice when a note arrives *is* the dynamic graph the fragment forbids.  A
fixed bank is not, so the feature is N copies of something the language
already handles — and the way to get N copies is to write them out, before
`classify`, as ordinary declarations.

**Nothing with a bit-identity obligation changes**, which is what these
tests are mostly about: the expansion produces a program the extractor, the
engine, the code generator and the oracle already understood, and the last
test here is the one that says so in the only way that counts.
"""

from __future__ import annotations

import shutil
import tempfile

import pytest

from gestate.audio import render
from gestate.audioengine import run
from gestate.audioextract import extract
from gestate.audiollvm import run_native
from gestate.audioschedule import Schedule
from gestate.audiovoices import VoicesError, banks_of, channels_of, expand

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the IR with")

#: A voice: one oscillator, its own filter, gated by the note's own times.
VOICE = """
Osc := Osc Float Int

hzOf : Int -> Float
hzOf k = 8.1758 * pow 2.0 (toFloat k / 12.0)

bump : Float -> Int -> Both Gate Note -> Osc
bump ph t nn = case nn of
    Both w q -> case w of
        Gate on off -> bend ph t q

bend : Float -> Int -> Note -> Osc
bend ph t q = case q of
    Note a b p -> Osc (wrap (ph + hzOf p / sampleRate)) (t + 1)

stepOsc : Osc -> Both Gate Note -> Osc
stepOsc o nn = case o of
    Osc ph t -> bump ph t nn

outOsc : Osc -> Float
outOsc o = case o of
    Osc ph t -> sawOf ph * 0.2

plucked : Sig Gate -> Sig Note -> Sig Float
plucked g s = pluckedFolded (!Both g s)

pluckedFolded : Sig (Both Gate Note) -> Sig Float
pluckedFolded s = lowpass 0.3 (map outOsc (scan stepOsc (Osc 0.0 0) s))
"""


def _program(count: int = 2, tail: str = "sound = lowpass 0.5 (gain 0.9 lead)"):
    return (f"""
Note := Note Int Int Int

voices lead {count} plucked : Sig Float
""" + VOICE + f"\nsound : Sig Float\n{tail}\n")


RATE, BLOCK = 4000, 64


# ── What it expands to ──────────────────────────────────────────────────────


def test_a_program_with_no_bank_is_untouched():
    """Nothing pays for this that does not use it — not even a parse."""
    source = "sound : Sig Float\nsound = map toFloat ticks\n"
    assert expand(source) is source


def test_the_authors_lines_do_not_move():
    """`audiospans` reports knobs by line, so the expansion may not shift any.

    Blanked in place and appended, rather than spliced — otherwise every
    line below a bank would slide and the editor would draw its knobs
    against the wrong ones.
    """
    source = _program()
    out = expand(source)
    before = source.splitlines()
    after = out.splitlines()[:len(before)]
    for i, (a, b) in enumerate(zip(before, after)):
        if a.startswith("voices ") or a.startswith("lead ="):
            assert b == "", f"line {i} should be blanked, got {b!r}"
        else:
            assert a == b, f"line {i} moved: {a!r} became {b!r}"


def test_the_bank_becomes_the_sum_of_its_voices():
    """The name is bound to the sum, so shaping it further is ordinary code."""
    out = expand(_program(3))
    assert "lead : Sig Float" in out
    line = next(l for l in out.splitlines() if l.startswith("lead = "))
    assert line.count("plucked lead") == 3
    assert line.count("addSig") == 2


def test_each_voice_gets_two_timing_channels_and_one_per_field():
    """`gateAt` and `offAt` come first, then the author's own record.

    The timing is *not* in the payload — see `Gate` in `audio.ges` — so a
    three-field record is five channels, not three.
    """
    out = expand(_program(2))
    for i in range(2):
        for j in range(5):
            assert f"leadChan{i}f{j} : Chan Int" in out
            assert f"leadChan{i}f{j} = chan" in out


def test_a_voice_runs_at_audio_rate():
    """The bug this found, and it was silent.

    A voice's parameters arrive on *control* channels, so a record built
    from those alone updates once per block — and a `scan` inside the voice
    would advance its oscillator once per block too.  The synth still
    plays.  Zipping `ticks` in is what makes it a synth rather than a very
    slow one.
    """
    out = expand(_program(1))
    assert "leadAtRate : Int -> Note -> Note" in out
    assert "leadGateAtRate : Int -> Gate -> Gate" in out
    # `zipSig`, not `zip`: this is `audiovoices` writing, and generated
    # code names the internal for the reason `desugar` does when it
    # expands `!` — a lift is not a method call the front end could make.
    assert "leadPayload0 = zipSig leadAtRate ticks leadRaw0" in out
    assert "leadGate0 = zipSig leadGateAtRate ticks leadRawGate0" in out

    # And it shows up where it matters: the clock is allocated at all.
    graph = extract(_program(2), rate=RATE)
    assert any(n.clock == "audio" for n in graph.nodes if n.kind == "source")


def test_the_channels_a_scheduler_writes_into_are_reported():
    """`channels_of` is the layout a note is delivered through."""
    source = _program(2)
    bank = banks_of(source)[0]
    assert (bank.name, bank.count, bank.record, bank.voice) == \
        ("lead", 2, "Note", "plucked")
    assert channels_of(source, bank) == [
        ["leadChan0f0", "leadChan0f1", "leadChan0f2", "leadChan0f3",
         "leadChan0f4"],
        ["leadChan1f0", "leadChan1f1", "leadChan1f2", "leadChan1f3",
         "leadChan1f4"]]


# ── Shapes and sizes ────────────────────────────────────────────────────────


@pytest.mark.parametrize("count", [1, 2, 5])
def test_a_bank_of_any_size_extracts(count):
    """One voice is a monophonic bank — not a special case, just N = 1."""
    graph = extract(_program(count), rate=RATE)
    assert len(graph.control_sources()) == 5 * count      # 2 timing + 3
    assert len({n.chan for n in graph.control_sources()}) == 5 * count


def test_each_voice_keeps_its_own_state():
    """Two voices, two oscillators, two filters — not one shared between them.

    And the filter *on the bank's sum* is a fifth, separate from both: a
    filter inside the voice function is per voice, and one applied to the
    bank's name is one for the lot.  Both work because a voice function is
    an ordinary signal transformation.
    """
    graph = extract(_program(2), rate=RATE)
    scans = [n.origin for n in graph.nodes if n.kind == "scan"]
    assert len(set(scans)) == len(scans), "two voices sharing a node"

    per_voice = [s for s in scans if s.startswith("sound/lead/")]
    assert sorted(per_voice) == [
        "sound/lead/plucked/pluckedFolded/lowpass/scan#0",
        "sound/lead/plucked/pluckedFolded/lowpass/scan#1",
        "sound/lead/plucked/pluckedFolded/scan#0",
        "sound/lead/plucked/pluckedFolded/scan#1"]
    assert [s for s in scans if not s.startswith("sound/lead/")] == [
        "sound/lowpass/scan#0"], "the filter on the sum is its own node"


@pytest.mark.parametrize("fields,record", [
    (1, "Note := Note Int"),
    (2, "Note := Note Int Int"),
    (4, "Note := Note Int Int Int Float"),
])
def test_a_record_of_any_width_is_folded_from_its_channels(fields, record):
    """1 is a `map`, 2 a single `zip`, and 3+ needs intermediates.

    A constructor is not a first-class function and `zip` takes two
    signals, so the shape of the generated builder changes with the width.
    """
    source = (f"\n{record}\n\nvoices lead 1 ident : Sig Float\n"
              "\nident : Sig Gate -> Sig Note -> Sig Float\n"
              "ident g s = !one s\n"
              "\none : Note -> Float\none n = 0.1\n"
              "\nsound : Sig Float\nsound = lead\n")
    graph = extract(source, rate=RATE)
    assert len(graph.control_sources()) == fields + 2


# ── What it refuses ─────────────────────────────────────────────────────────


def test_the_two_part_spelling_is_retired_by_name():
    """`voices lead 2 : Note -> Sig Float` + `lead = voice` was the old
    way to say it, and it is refused *as itself*: a stray old file gets
    told what to write, not silently accepted — silent compatibility is
    where this project's longest evenings came from."""
    source = "\nNote := Note Int\n\nvoices lead 2 : Note -> Sig Float\n"
    with pytest.raises(VoicesError, match="retired"):
        expand(source)
    with pytest.raises(VoicesError, match="voices lead 2 <voice>"):
        expand(source + "lead = f\n")


def test_a_bank_naming_no_data_type_is_refused():
    source = ("\nvoices lead 2 f : Sig Float\n"
              "\nf : Sig Gate -> Sig Note -> Sig Float\n")
    with pytest.raises(VoicesError, match="nor a data type declared here"):
        expand(source)


def test_a_line_that_is_not_a_full_signature_is_not_a_bank():
    """`voices lead 2 : Note` no longer declares one.

    The declaration is the voice function's own signature now, so a line
    missing its result type is not a bank — and is left alone to be
    rejected by the parser, which is the right reader for a syntax error.
    """
    assert expand("\nvoices lead 2 : Note\n") == "\nvoices lead 2 : Note\n"


def test_a_frame_bank_sums_componentwise():
    """`addSig` is `Sig Float` only, so a stereo bank gets its own adder."""
    source = ("\nNote := Note Int\nStereo := Stereo Float Float\n"
              "\nvoices wide 2 breathy : Sig Stereo\n"
              "\nbreathy : Sig Gate -> Sig Note -> Sig Stereo\n")
    out = expand(source)
    assert "wide : Sig Stereo" in out
    assert "zipSig wideAdd" in out
    assert "addSig" not in out, "a frame cannot be summed with `addSig`"
    assert "wideAdd : Stereo -> Stereo -> Stereo" in out


def test_a_frame_of_something_other_than_floats_is_refused():
    """Every field of a frame is an output channel, so every field is a sample."""
    source = ("\nNote := Note Int\nOdd := Odd Float Int\n"
              "\nvoices wide 2 f : Sig Odd\n"
              "\nf : Sig Gate -> Sig Note -> Sig Odd\n")
    with pytest.raises(VoicesError, match="not a frame"):
        expand(source)


def test_a_record_with_several_constructors_is_refused():
    source = ("\nNote := A Int | B Int\n\nvoices lead 2 f : Sig Float\n"
              "\nf : Sig Gate -> Sig Note -> Sig Float\n")
    with pytest.raises(VoicesError, match="2 constructors"):
        expand(source)


def test_a_field_that_is_not_a_control_value_is_refused():
    """Every field becomes a control channel, and those carry one slot."""
    source = ("\nInner := Inner Int\nNote := Note Inner\n"
              "\nvoices lead 2 f : Sig Float\n"
              "\nf : Sig Gate -> Sig Note -> Sig Float\n")
    with pytest.raises(VoicesError, match="one slot"):
        expand(source)


def test_a_record_with_no_fields_is_refused():
    source = ("\nNote := Note\n\nvoices lead 2 f : Sig Float\n"
              "\nf : Sig Gate -> Sig Note -> Sig Float\n")
    with pytest.raises(VoicesError, match="nothing to play"):
        expand(source)


def test_two_banks_of_the_same_name_are_refused():
    source = ("\nNote := Note Int\n\nvoices lead 2 f : Sig Float\n"
              "\nvoices lead 3 g : Sig Float\n")
    with pytest.raises(VoicesError, match="both called"):
        expand(source)


def test_a_bank_of_no_voices_is_refused():
    source = "\nNote := Note Int\n\nvoices lead 0 f : Sig Float\n"
    with pytest.raises(VoicesError, match="at least one voice"):
        expand(source)


# ── The comparison that matters ─────────────────────────────────────────────


@needs_clang
def test_a_bank_plays_the_same_through_all_three_engines():
    """The claim the whole expansion rests on.

    It generates ordinary declarations, so the extractor, the block
    renderer, the code generator and the oracle see a program they already
    understood — and the only way to say that is to render it three ways
    and compare.  Driven by a schedule, since that is how notes arrive.
    """
    source = _program(3)
    graph = extract(source, rate=RATE)
    schedule = Schedule()
    for i, pitch in enumerate((60, 64, 67)):
        schedule.change(0, f"leadChan{i}f0", 1)        # gateAt
        schedule.change(0, f"leadChan{i}f4", pitch)    # payload field 2
    control = schedule.control_for(graph)
    samples = 300

    oracle = render(source, samples / RATE, RATE,
                    control_every=BLOCK, schedule=schedule)
    assert run(graph, samples, block=BLOCK, control=control) == oracle
    with tempfile.TemporaryDirectory() as d:
        assert run_native(graph, d, samples, block=BLOCK,
                          control=control) == oracle
    assert max(abs(s) for s in oracle) > 0.05, "silent"


def test_the_voices_are_actually_independent():
    """Three pitches must not sound like three of the same pitch."""
    source = _program(3)
    graph = extract(source, rate=RATE)

    def at(pitches):
        s = Schedule()
        for i, p in enumerate(pitches):
            s.change(0, f"leadChan{i}f0", 1)
            s.change(0, f"leadChan{i}f4", p)
        return run(graph, 300, block=BLOCK, control=s.control_for(graph))

    assert at((60, 64, 67)) != at((60, 60, 60))
    assert at((60, 64, 67)) != at((67, 64, 60)), "voices are interchangeable"


# ── The declaration says what it is ─────────────────────────────────────────
#
# `voices lead 4 sineVoice : Sig Float`.  The older spelling — a signature
# and an equation, with the payload written a second time — reads like a
# supercombinator and is not one: the "equation" may only ever be a bare
# name, and the "signature" is a line the parser never sees.
# `spec/frp_lesson.md`: "if it's not a supercombinator, it shouldn't look
# like one either".  Both are accepted; this is the one to write.

INLINE = """Key := Key Int Int

voices lead 2 sineVoice : Sig Float

sineVoice : Sig Gate -> Sig Key -> Sig Float
sineVoice g s = !one s

one : Key -> Float
one q = 0.1

sound : Sig Float
sound = lead
"""


def test_the_voice_is_written_where_the_bank_is_declared():
    out = expand(INLINE)
    assert "lead : Sig Float" in out
    assert "sineVoice leadGate0 leadPayload0" in out
    assert "sineVoice leadGate1 leadPayload1" in out


def test_the_older_spelling_of_the_same_bank_is_refused():
    """It used to expand identically; now it is named and turned away."""
    older = INLINE.replace("voices lead 2 sineVoice : Sig Float",
                           "voices lead 2 : Key -> Sig Float\nlead = sineVoice")
    with pytest.raises(VoicesError, match="retired"):
        expand(older)


def test_the_payload_comes_from_the_voices_own_signature():
    """Said once, where the voice already had to say it.

    Written twice it can disagree, and the disagreement is silent: the bank
    would open channels for one record and hand the voice another.
    """
    graph = extract(INLINE, rate=RATE)
    # Two timing channels and the payload's two fields, per voice.
    assert len(graph.control_sources()) == 2 * (2 + 2)


def test_a_bare_int_is_a_payload():
    """A note number is one control value, which is all a field ever is.

    Being told to declare `Key := Key Int` to play one was ceremony with
    nothing behind it — `spec/frp_lesson.md` asked this first.
    """
    source = ("\nvoices lead 2 keyVoice : Sig Float\n"
              "\nkeyVoice : Sig Gate -> Sig Int -> Sig Float\n"
              "keyVoice g s = !one s\n"
              "\none : Int -> Float\none n = 0.1\n"
              "\nsound : Sig Float\nsound = lead\n")
    out = expand(source)
    assert "leadMk0" not in out, "a scalar payload has nothing to build"
    graph = extract(source, rate=RATE)
    assert len(graph.control_sources()) == 2 * (2 + 1)


def test_a_voice_may_be_an_expression():
    """`voices lead 2 (pluck punchy) : Sig Float` — an applied voice.

    The older spelling's equation could hold a name and nothing else, so an
    instrument that took a parameter had to be given a second name for the
    sake of the declaration.
    """
    source = ("\npunchy : Adsr\npunchy = Adsr 0.01 0.1 0.5 0.1\n"
              "\nvoices lead 2 (pluck punchy) : Sig Float\n"
              "\npluck : Adsr -> Sig Gate -> Sig Int -> Sig Float\n"
              "pluck e g s = adsr e g\n"
              "\nsound : Sig Float\nsound = lead\n")
    out = expand(source)
    assert "(pluck punchy) leadGate0 leadPayload0" in out
    assert extract(source, rate=RATE).channels() == 1


def test_a_voice_with_no_signature_is_refused_and_says_what_to_write():
    source = ("\nvoices lead 2 mystery : Sig Float\n"
              "\nsound : Sig Float\nsound = lead\n")
    with pytest.raises(VoicesError, match="has no type signature"):
        expand(source)


def test_a_voice_that_is_handed_no_note_is_refused():
    source = ("\nvoices lead 2 plain : Sig Float\n"
              "\nplain : Sig Float -> Sig Float\nplain s = s\n"
              "\nsound : Sig Float\nsound = lead\n")
    with pytest.raises(VoicesError, match="is not a voice"):
        expand(source)


# ── What a bank reading may be handed twice — `fixme.md` F99 ────────────────


BANKED = """Note := Note Int Int

voices lead 3 sineVoice : Sig Float

sineVoice : Sig Gate -> Sig Note -> Sig Float
sineVoice g s = sine (!hzOf s) * adsr (Adsr 0.01 0.2 0.6 0.2) g

hzOf : Note -> Float
hzOf (Note k v) = keyHz k

sound : Sig Float
sound = gain 0.4 lead
"""


def test_a_bank_reading_is_kept_and_handed_out_as_copies():
    """`_prepare` *parses* the program once per bank to read each payload,
    and `channels_of` asks once per bank — a second of it for a file with
    four.  So the reading is kept; but a `Bank` is mutable, so what each
    caller gets is its own.
    """
    from gestate.audiovoices import banks_of

    first, second = banks_of(BANKED), banks_of(BANKED)
    assert first == second
    assert first[0] is not second[0], "one caller must not reach another's"

    first[0].name = "scribbled on"
    assert banks_of(BANKED)[0].name == "lead"


def test_expanding_the_same_program_twice_is_the_same_text():
    from gestate.audiovoices import expand

    once = expand(BANKED)
    expand.cache_clear()
    assert expand(BANKED) == once
