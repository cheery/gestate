"""`voices` — a bank of N copies of one voice, expanded before compilation.

    voices lead 8 plucked : Sig Float

    plucked : Sig Gate -> Sig Int -> Sig Float
    plucked g s = saw (!keyHz s) * perc 6.0 g

    sound = lowpass 0.4 (gain 0.8 lead)

**The declaration says what it is** — a bank of eight `plucked`, and the
name `lead` is a `Sig Float`.  What a note *carries* is read off the
voice's own signature rather than written a second time here, and it may be
a record or a bare `Int`/`Float`: every field of a payload is one control
value, and a note number is one.  An earlier spelling put the payload in
the declaration and the voice in a separate `lead = plucked` equation,
which reads as a supercombinator while being neither; it is still accepted
and `spec/frp_lesson.md` is why it should not be written.

**The bank's name is bound to its sum.**  `lead : Sig Float` is the eight
voices added together, so shaping the bank further is ordinary signal code —
a filter on `lead` is one filter for the whole bank, and a filter *inside*
`plucked` is one per voice.  Both work because a voice function is an
ordinary signal transformation; neither needed anything added for it.

**Why a source-to-source expansion.**  Polyphony is the one thing the static
fragment cannot express: allocating a voice when a note arrives is exactly
the dynamic graph the fragment exists to forbid.  A *fixed* bank is not —
eight voices is eight subgraphs, known at compile time — so the whole
feature is N copies of something the language already handles, and the way
to get N copies is to write them out.

That is why this runs before `classify` and generates ordinary
declarations: the extractor, the engine, the code generator and the oracle
all see a program they already understood, and **nothing with a
bit-identity obligation changes**.  Allocation — which note goes to which
voice — is host policy, the same place knob values come from.

**Line numbers are preserved.**  The `voices` line and the equation that
names the voice function are blanked in place rather than deleted, and the
generated declarations are *appended*.  Otherwise every line below a bank
would shift, and `audiospans` would report knobs against the wrong ones.

A generated channel therefore has no source position, which is right rather
than merely tolerable: note channels are driven by a scheduler, not turned
by hand, so the editor does not sprout a slider for each one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

#: `voices <name> <count> <voice> : Sig <Result>` — **the form to write**.
#:
#: It says what it is: a bank called `<name>` of `<count>` copies of
#: `<voice>`, and the name it binds is `Sig <Result>`, which is exactly the
#: type the rest of the program sees.  `-> Sig Stereo` is a bank whose
#: voices are stereo, and the sum it produces is stereo too.
#:
#: The payload is **not** written here.  It is read off the voice's own
#: signature — `sineVoice : Sig Gate -> Sig Key -> Sig Float` says `Key` — so
#: there is one place a bank's notes are described and it is the definition
#: that reads them.  `spec/frp_lesson.md` asked for both halves of this:
#: the instrument written where the bank is declared, and a payload that
#: may be an `Int` rather than only a record.
_DECL_INLINE = re.compile(
    r"^voices\s+([A-Za-z_]\w*)\s+(\d+)\s+(\S.*?)"
    r"\s*:\s*Sig\s+([A-Za-z_]\w*)\s*$")

#: `voices <name> <count> : <Record> -> Sig <Result>`, with the voice named
#: by a separate `<name> = <fn>` equation — **the older spelling**.
#:
#: Kept because files are written in it, and refused nothing: it is the
#: same bank.  What it got wrong is that it *looks* like a supercombinator
#: — a signature and an equation — while being neither, so a reader learns
#: a shape the language does not have, and the equation may only ever be a
#: bare name.  `spec/frp_lesson.md`: "if it's not a supercombinator, it
#: shouldn't look like one either".
_DECL = re.compile(
    r"^voices\s+([A-Za-z_]\w*)\s+(\d+)\s*:\s*([A-Za-z_]\w*)"
    r"\s*->\s*Sig\s+([A-Za-z_]\w*)\s*$")

#: The types a bank's record may be made of.  Each field becomes a *control
#: channel*, and a control value is one slot, so the rule is the extractor's
#: rather than one invented here.  The value is what an untouched channel
#: holds before the scheduler says otherwise.
_FIELD_DEFAULT = {"Int": "0", "Float": "0.0"}


class VoicesError(Exception):
    pass


@dataclass
class Bank:
    """One `voices` declaration, as written."""
    name: str
    count: int
    record: str
    #: What one voice produces — `Float` for a mono bank, or a record of
    #: `Float`s for a frame.  The bank's sum has this type too.
    result: str
    #: The line it was on, 0-based, so it can be blanked.
    line: int
    #: The voice — an expression in the declaration, or the right-hand side
    #: of the older spelling's `name = <fn>` equation, whose line this is.
    voice: str = ""
    voice_line: int = -1

    @property
    def declaration(self) -> str:
        """How it was written, for a message to quote back."""
        if self.voice_line >= 0:
            return (f"voices {self.name} {self.count} : {self.record} "
                    f"-> Sig {self.result}")
        return (f"voices {self.name} {self.count} {self.voice} "
                f": Sig {self.result}")

    @property
    def applied(self) -> str:
        """The voice, ready to be applied to a note signal.

        Parenthesised unless it is a bare name or already wrapped, because
        the declaration admits an expression and `myVoice env note0` would
        apply the wrong thing to the wrong number of arguments.
        """
        voice = self.voice
        if voice.isidentifier() or _is_wrapped(voice):
            return voice
        return f"({voice})"


def _is_wrapped(expr: str) -> bool:
    """Is the whole expression already inside one pair of parentheses?

    `(pluck punchy)` is; `(f x) (g y)` is not, and wrapping the second is
    what keeps it one argument.
    """
    if not (expr.startswith("(") and expr.endswith(")")):
        return False
    depth = 0
    for i, ch in enumerate(expr):
        depth += (ch == "(") - (ch == ")")
        if depth == 0:
            return i == len(expr) - 1
    return False


def _banks(lines: list) -> list:
    out = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # The older spelling first: its `: <Record> -> Sig <Result>` would
        # otherwise have to be excluded from the inline form's voice
        # expression, and trying the narrower pattern first says the same
        # thing without a lookahead.
        match = _DECL.match(stripped)
        if match is not None:
            # **The two-part spelling is retired, by name.**  It was
            # `voices lead 2 : Note -> Sig Float` above a `lead = voice`
            # line; accepting it silently is how it survived long enough
            # to be copied out of an old test into three new pieces.  A
            # stray old file is told exactly what to write instead.
            name, count, record, result = match.groups()
            raise VoicesError(
                f"`voices {name} {count} : {record} -> {result}` is the "
                f"retired two-part spelling.  Name the voice in the "
                f"declaration — `voices {name} {count} <voice> : {result}` "
                f"— and drop the `{name} = <voice>` line: the payload type "
                f"now comes from the voice's own signature")
        match = _DECL_INLINE.match(stripped)
        if match is None:
            continue
        name, count, voice, result = match.groups()
        # Filled in from the voice's own signature once the program can
        # be parsed — see `_payload_of`.
        record_known = ""
        if int(count) < 1:
            raise VoicesError(
                f"`voices {name} {count}` — a bank needs at least one voice")
        out.append(Bank(name=name, count=int(count), record=record_known,
                        result=result, line=i, voice=voice,
                        voice_line=-1))
    return out


def _module(source: str):
    """`source`, parsed once — every reader below asks for declarations
    out of the same text.

    The text is the program with the prelude in front of it, thousands of
    lines, and there are several questions per bank: measured on
    `quartet.ges`, parsing per question was seventeen parses and eleven
    seconds of the editor's start.  The readers only *read* the module, so
    `prelude._parsed`'s one shared cache can serve them all.
    """
    from .prelude import _parsed

    return _parsed(source)


def _payload_of(source: str, bank: Bank) -> str:
    """What this bank's notes carry, read off its voice's signature.

    A voice is `Sig Gate -> Sig a -> Sig b`, so the payload is the `a` —
    and the voice's definition is where an author has already had to say
    it.  Asking for it a second time in the declaration is how the two come
    to disagree, and the disagreement is silent: a bank would open channels
    for one record and hand the voice another.

    The *head* of the voice expression is what carries the signature, so
    `voices lead 4 (tine piano) : Sig Float` reads `tine`'s — an applied
    voice still says what a note is.
    """
    from .syntax.ast import VSig

    # An *applied* voice — `(tine piano)` — has its first parameters
    # already supplied, so the two signals are that many places along.
    words = bank.voice.strip("()").split() if bank.voice else [""]
    head, supplied = words[0], len(words) - 1
    try:
        module = _module(source)
    except Exception as exc:                            # noqa: BLE001
        raise VoicesError(f"could not read the program: {exc}") from None

    sig = next((i for i in module.items
                if isinstance(i, VSig) and i.name == head), None)
    if sig is None:
        raise VoicesError(
            f"`{bank.declaration}` — `{head}` has no type signature, and "
            f"the bank reads what its notes carry off one.  Give it "
            f"`{head} : Sig Gate -> Sig <Payload> -> Sig {bank.result}`")

    params = _arrow_parts(sig.type_)[supplied:]
    gate = params[0] if params else None
    payload = params[1] if len(params) > 1 else None
    if not (_names_sig_of(gate) == "Gate" and _names_sig_of(payload)):
        raise VoicesError(
            f"`{bank.declaration}` — `{head}` is not a voice.  One is "
            f"handed two signals: `{head} : Sig Gate -> Sig <Payload> -> "
            f"Sig {bank.result}`, where `Gate` says when the note began "
            f"and when it was released, and the payload is this program's "
            f"own")
    return _names_sig_of(payload)


def _arrow_parts(type_ast) -> list:
    """The `->`-separated parts of a signature, left to right.

    Before fixity resolution an arrow is a flat `VOpPhrase` whose `atoms`
    alternate operand, operator, operand — so the parts are the operands
    around each `"->"`, and a signature with no arrow at all is one part.
    """
    from .syntax.ast import VOpPhrase

    if not isinstance(type_ast, VOpPhrase):
        return [type_ast]
    return [a for i, a in enumerate(type_ast.atoms) if i % 2 == 0]


def _names_sig_of(node) -> str:
    """`Sig X` → `"X"`, for anything else `""`.

    `Sig (Played Key)` is deliberately not accepted: the bundled form is
    the one this replaced, and a voice still written against it should be
    told so by name rather than have its payload guessed.
    """
    from .syntax.ast import VApp, VConId

    if not (isinstance(node, VApp) and isinstance(node.fn, VConId)
            and node.fn.value == "Sig"):
        return ""
    return node.arg.value if isinstance(node.arg, VConId) else ""


def _find_voice(bank: Bank, lines: list) -> None:
    """Attach the older spelling's `name = <fn>` equation.

    Only for a declaration that has one: the inline form carries its voice
    where a reader looks for it.  A bare name is all this can ever accept,
    which is the limitation that made the equation worth removing — it
    reads as a definition and admits none of what a definition admits.
    """
    if bank.voice:
        return
    pattern = re.compile(rf"^{bank.name}\s*=\s*([A-Za-z_]\w*)\s*$")
    for i, line in enumerate(lines):
        match = pattern.match(line.strip())
        if match is not None:
            bank.voice, bank.voice_line = match.group(1), i
            return
    raise VoicesError(
        f"`voices {bank.name} {bank.count} : {bank.record} -> Sig "
        f"{bank.result}` has no `{bank.name} = <voice>` to say what a "
        f"voice is")


def _prepare(lines: list, banks: list) -> str:
    """Attach each bank's voice and payload; return the blanked program.

    The order is forced.  A voice named by the older spelling's equation
    has to be found while the line is still there, blanking has to happen
    before anything can *parse* the program — a `voices` line is not
    gestate syntax — and the payload is read out of the parsed result.
    """
    for bank in banks:
        _find_voice(bank, lines)
    blanked = _blank(lines, banks)
    for bank in banks:
        if not bank.record:
            bank.record = _payload_of(blanked, bank)
    return blanked


def _blank(lines: list, banks: list) -> str:
    """The program with every `voices` line and its equation blanked.

    Needed before the source can be *parsed* at all: `voices lead 4 : Note -> Sig Float`
    is not gestate syntax, which is the point of expanding it, and the
    parser reaches it before anything here can.  Blanked rather than
    dropped so that line numbers do not move — see the module docstring.
    """
    out = list(lines)
    for bank in banks:
        out[bank.line] = ""
        if bank.voice_line >= 0:
            out[bank.voice_line] = ""
    return "\n".join(out)


def _is_scalar(record: str) -> bool:
    """Is the payload a bare `Int` or `Float` rather than a record?

    **A one-field record is what a bank already generates**, and `Int` is
    one field, so a payload that is just a note number was refused for no
    reason anyone could give: the rule is "every field is a control value",
    and an `Int` satisfies it without a wrapper.  Being told to declare
    `Key := Key Int` to play a note number is exactly the ceremony
    `spec/frp_lesson.md` is about.

    What differs downstream is only that there is no constructor to fold
    the channel into — the channel *is* the payload — so `_builders` emits
    no maker and `_voice` uses the channel's signal directly.
    """
    return record in _FIELD_DEFAULT


def _fields(source: str, record: str, bank: str) -> list:
    """The field types of `record`'s single constructor.

    `source` must already have its `voices` lines blanked — see `_blank`.

    Read from the real parser rather than matched out of the text: a data
    declaration can be spread over lines, carry `deriving`, or have type
    parameters, and a regex that got any of those wrong would fail somewhere
    much later.

    A list off a cached tuple, because that parse is the same one for every
    bank of a program and `channels_of` asks per bank — see `_prepared`.
    """
    return list(_field_types(source, record, bank))


@lru_cache(maxsize=8)
def _field_types(source: str, record: str, bank: str) -> tuple:
    from .syntax.ast import VConId, VTypeDecl

    if _is_scalar(record):
        return (record,)

    try:
        module = _module(source)
    except Exception as exc:                            # noqa: BLE001
        raise VoicesError(f"could not read the program: {exc}") from None

    decl = next((i for i in module.items
                 if isinstance(i, VTypeDecl) and i.name == record), None)
    if decl is None:
        allowed = " or ".join(sorted(_FIELD_DEFAULT))
        raise VoicesError(
            f"the bank `{bank}` plays `{record}`, which is neither "
            f"{allowed} nor a data type declared here")
    if len(decl.constructors) != 1:
        raise VoicesError(
            f"`{record}` has {len(decl.constructors)} constructors; a voice's "
            f"parameters are one record, so it needs exactly one")

    fields = []
    for field in decl.constructors[0].fields:
        if not isinstance(field, VConId) or field.value not in _FIELD_DEFAULT:
            allowed = " or ".join(sorted(_FIELD_DEFAULT))
            raise VoicesError(
                f"`{record}` has a field this bank cannot supply: every field "
                f"becomes a control channel, and a control value is one slot, "
                f"so each must be {allowed}")
        fields.append(field.value)
    if not fields:
        raise VoicesError(
            f"`{record}` has no fields, so a voice would have nothing to play")
    return tuple(fields)


@lru_cache(maxsize=8)
def _type_decls(source: str) -> tuple:
    """Every `T := …` in `source`, parsed once.

    Cached because the *prelude* is one of the two texts this is asked
    about and it is the same text every time — see `_frame`, which looks a
    frame type up in the program and then in the prelude.
    """
    from .syntax.ast import VTypeDecl

    if not source.strip():
        return ()
    return tuple(i for i in _module(source).items
                 if isinstance(i, VTypeDecl))


def _frame(source: str, bank: Bank, prelude: str = "") -> list:
    """The `Float` fields a voice's result is made of — `[]` for mono.

    A frame is a record of `Float`s and nothing else: it is what leaves the
    engine per instant, one number per output channel, so a field that was
    not a `Float` would be a channel that is not a sample.

    Looked for in the program **and then in the prelude**, because
    `synth.ges` declares `Stereo` so that two programs mean the same thing
    by a stereo frame.  Without the second place a bank could only be
    stereo by redeclaring the type it was already given.
    """
    from .syntax.ast import VConId

    if bank.result == "Float":
        return []
    decls = _type_decls(source) + _type_decls(prelude)
    decl = next((i for i in decls if i.name == bank.result), None)
    if decl is None:
        raise VoicesError(
            f"`voices {bank.name} … -> Sig {bank.result}` names no data "
            f"type in this program or the prelude; a voice produces "
            f"`Float`, or a record of `Float`s for a frame")
    if len(decl.constructors) != 1:
        raise VoicesError(
            f"`{bank.result}` has {len(decl.constructors)} constructors; a "
            f"frame is one record")
    fields = decl.constructors[0].fields
    if not fields or any(not isinstance(f, VConId) or f.value != "Float"
                         for f in fields):
        raise VoicesError(
            f"`{bank.result}` is not a frame: every field must be `Float`, "
            f"because each one is an output channel")
    return [f.value for f in fields]


# ── Generating ──────────────────────────────────────────────────────────────


def _cap(name: str) -> str:
    return name[0].upper() + name[1:]


def _builders(bank: Bank, fields: list) -> list:
    """The functions that fold k channels into one record.

    Three things force this shape rather than something shorter.  A
    constructor is **not a first-class function** in gestate, so `zipSig
    Note a b` does not typecheck and a wrapper is needed.  `zipSig` combines
    **two** signals, so k fields need k-1 of them.  And the intermediate
    types cannot be *tuples*, because the extractor has a layout for `Int`,
    `Float` and user data types and for nothing else — so this declares its
    own.
    """
    k = len(fields)
    out = [f"# ── generated for `{bank.declaration}` ──",
           # **A voice must run at audio rate.**  Its parameters arrive on
           # control channels, so a signal built from those alone updates
           # once per *block* — and a `scan` inside the voice would advance
           # its oscillator once per block too.  That is silent: the synth
           # plays, an octave and a half flat and wrong in a way no error
           # reports.  Zipping `ticks` in makes a signal audio-rate while
           # the control values are held across the block, which is exactly
           # the `.kr → .ar` boundary `sync` was given for.  Both of a
           # voice's signals get it: either one alone could drive a `scan`.
           f"{bank.name}GateAtRate : Int -> Gate -> Gate",
           f"{bank.name}GateAtRate n v = v", "",
           f"{bank.name}AtRate : Int -> {bank.record} -> {bank.record}",
           f"{bank.name}AtRate n v = v", "",
           # `Gate on off` from the two timing channels.
           f"{bank.name}MkGate : Int -> Int -> Gate",
           f"{bank.name}MkGate a b = Gate a b", ""]
    if _is_scalar(bank.record):
        # Nothing to build: the channel carries the payload itself.
        return out
    if k == 1:
        out += [f"{bank.name}Mk0 : {fields[0]} -> {bank.record}",
                f"{bank.name}Mk0 a0 = {bank.record} a0", ""]
        return out

    for j in range(1, k):
        last = j == k - 1
        result = bank.record if last else f"{_cap(bank.name)}Part{j}"
        if not last:
            out += [f"{result} := {result} " + " ".join(fields[:j + 1]), ""]
        args = " ".join(f"a{i}" for i in range(j + 1))
        if j == 1:
            out += [f"{bank.name}Mk1 : {fields[0]} -> {fields[1]} -> {result}",
                    f"{bank.name}Mk1 a0 a1 = {result} {args}", ""]
        else:
            prev = f"{_cap(bank.name)}Part{j - 1}"
            bound = " ".join(f"a{i}" for i in range(j))
            out += [f"{bank.name}Mk{j} : {prev} -> {fields[j]} -> {result}",
                    f"{bank.name}Mk{j} p a{j} = case p of",
                    f"    {prev} {bound} -> {result} {args}", ""]
    return out


#: The two channels every voice has before its payload's: when the note
#: starts, and when it ends.  Their positions are `audioalloc.GATE_AT` and
#: `OFF_AT`, and a payload's own field `j` is channel `j + TIMING`.
TIMING = ("Int", "Int")


def _voice(bank: Bank, fields: list, i: int) -> list:
    """One voice: its channels, and the two signals it is handed.

    Channel `f0` is `gateAt` and `f1` is `offAt`; the payload's fields
    follow.  The timing is *not* part of the author's record — see `Gate`
    in `audio.ges` — and it is no longer folded into one either: the voice
    receives `Sig Gate` and `Sig <payload>` and reads whichever it needs.
    """
    out = []
    for j, type_ in enumerate(TIMING + tuple(fields)):
        chan = f"{bank.name}Chan{i}f{j}"
        out += [f"{chan} : Chan {type_}",
                f"{chan} = chan",
                f"{bank.name}Sig{i}f{j} : Sig {type_}",
                f"{bank.name}Sig{i}f{j} = {_FIELD_DEFAULT[type_]} ::: "
                f"mkSig (wait {chan})", ""]

    payload = f"{bank.name}Payload{i}"
    base = len(TIMING)

    # The author's record, from the channels after the timing ones.
    if _is_scalar(bank.record):
        # A scalar payload *is* its channel — there is no record to fold it
        # into, so the signal the channel already carries is the payload.
        raw_payload = f"{bank.name}Sig{i}f{base}"
    elif len(fields) == 1:
        raw_payload = f"{bank.name}Raw{i}"
        out += [f"{raw_payload} : Sig {bank.record}",
                f"{raw_payload} = mapSig {bank.name}Mk0 "
                f"{bank.name}Sig{i}f{base}", ""]
    else:
        acc = f"{bank.name}Sig{i}f{base}"
        for j in range(1, len(fields)):
            last = j == len(fields) - 1
            target = (f"{bank.name}Raw{i}" if last
                      else f"{bank.name}Acc{i}p{j}")
            type_ = bank.record if last else f"{_cap(bank.name)}Part{j}"
            out += [f"{target} : Sig {type_}",
                    f"{target} = zipSig {bank.name}Mk{j} {acc} "
                    f"{bank.name}Sig{i}f{j + base}", ""]
            acc = target
        raw_payload = acc

    # The gate, from the two timing channels — and both signals brought to
    # audio rate, for the reason `_builders` gives at `AtRate`.
    out += [f"{bank.name}RawGate{i} : Sig Gate",
            f"{bank.name}RawGate{i} = zipSig {bank.name}MkGate "
            f"{bank.name}Sig{i}f0 {bank.name}Sig{i}f1", "",
            f"{bank.name}Gate{i} : Sig Gate",
            f"{bank.name}Gate{i} = zipSig {bank.name}GateAtRate ticks "
            f"{bank.name}RawGate{i}", "",
            f"{payload} : Sig {bank.record}",
            f"{payload} = zipSig {bank.name}AtRate ticks {raw_payload}", ""]
    return out


def _adder(bank: Bank, frame: list) -> tuple:
    """`(declarations, the combinator that sums two voices)`.

    `addSig` for a mono bank, and a generated componentwise adder for a
    frame — a stereo bank sums left with left and right with right, which
    `addSig` cannot do because it is `Sig Float` only.  Generated per bank
    rather than added to `signal.ges`, since the frame type is the
    program's and the prelude has never seen it.
    """
    if bank.result == "Float":
        return [], "addSig"

    fields = " ".join(f"a{i} + b{i}" for i in range(len(frame)))
    lhs = " ".join(f"a{i}" for i in range(len(frame)))
    rhs = " ".join(f"b{i}" for i in range(len(frame)))
    name = f"{bank.name}Add"
    return ([f"{name} : {bank.result} -> {bank.result} -> {bank.result}",
             f"{name} x y = case x of",
             f"    {bank.result} {lhs} -> {name}To y {lhs}", "",
             f"{name}To : {bank.result} -> "
             + " -> ".join(["Float"] * len(frame)) + f" -> {bank.result}",
             f"{name}To y {lhs} = case y of",
             f"    {bank.result} {rhs} -> {bank.result} "
             + " ".join(f"({a} + {b})" for a, b in
                        zip(lhs.split(), rhs.split())), ""],
            f"zipSig {name}")


#: `instance FromMIDI <Record>` — written in the program, or not.
_INSTANCE = r"^\s*instance\s+FromMIDI\s+{}\s*(where)?\s*$"


def _takes_midi(source: str, record: str) -> bool:
    """Does the program say how this payload comes from a MIDI note?"""
    import re as _re

    return _re.search(_INSTANCE.format(_re.escape(record)), source,
                      _re.M) is not None


def _from_midi(bank: Bank, source: str) -> list:
    """A forwarder, so the instance survives to be *called* by the host.

    Only reachable definitions are compiled, and nothing in a synth calls
    `noteOn` — the caller is Python, holding a keyboard.  So the method
    would be dropped before the host could reach it, and a top-level
    definition is what makes it a root.

    Generated only when the program declares the instance.  Emitting it
    regardless would turn a *missing* instance — which should grey out a
    checkbox — into a type error that stops the synth compiling at all.
    """
    if not _takes_midi(source, bank.record):
        return []
    return [f"{bank.name}FromMidi : Int -> Int -> Int -> Maybe {bank.record}",
            f"{bank.name}FromMidi ch p v = noteOn ch p v", ""]


def _voice_type(banks: list) -> list:
    """`Voice`, and the injection each bank offers.

    `Voice` is the opaque type `music.ges` names in `Assigned Voice` — a sum
    over the banks this program declares, each constructor carrying that
    bank's own payload.  It is generated because only the program knows what
    its banks are, and it is *opaque* because nothing in gestate ever takes
    it apart: the host reads the constructor's tag for the bank and its
    arguments for the payload, exactly as `midi.py` reads `Midi`/`Perc`.

    `voicesLead : Custom -> [: a :]` is parametric in `a` for the same
    reason `instrument` is — `Assigned` carries no payload of type `a` — and
    that is what keeps `[: Void :]` proving every note was assigned.
    """
    out = ["Voice := " + "\n         | ".join(
        f"{_cap(b.name)}Note {b.record}" for b in banks), ""]
    for bank in banks:
        out += [f"voices{_cap(bank.name)} : {bank.record} -> [: a :]",
                f"voices{_cap(bank.name)} x = "
                f"Assigned ({_cap(bank.name)}Note x)", ""]
    return out


def _sum(bank: Bank, frame: list) -> list:
    """`name : Sig <result>` — the bank's voices added together.

    The bank's name is bound to the **sum** so that shaping it further is
    ordinary signal code: `lowpass 0.4 lead` filters the whole bank, and a
    filter inside the voice function filters each voice.
    """
    decls, add = _adder(bank, frame)
    voice = bank.applied
    one = lambda i: f"{voice} {bank.name}Gate{i} {bank.name}Payload{i}"
    expr = one(0)
    for i in range(1, bank.count):
        expr = f"{add} ({expr}) ({one(i)})"
    return decls + [f"{bank.name} : Sig {bank.result}",
                    f"{bank.name} = {expr}", ""]


_SINK = None
_CANVAS = None
_NOTES = None


def _sinks(source: str) -> str:
    """Rewrite every `sink <expr>` into a hidden ordinary definition.

    The scope-dropping tool (roadmap §"Dropping a scope in one move",
    Henri's pick): `sink scope "stab" stab` keeps an observer alive
    beside the sound without touching the definition being observed —
    the edit is one appended line and its undo is one line.  One line
    becomes one line — `__sink_<k>__ = <expr>` — so positions never
    move, the promise `_blank` already keeps.  Numbered in reading
    order: adding a sink above another renumbers the ones below,
    which resets their scope rings and nothing else, and a
    diagnostic's state is 93 ms of picture.

    Top level only — an indented `sink` is somebody's own word — and
    a comment's `sink` is a comment.

    **And the `canvas` line, the same shape** (B2, `spec/workbench.md`
    §"Content boxes"): a bare `canvas` at top level is the ask for the
    walked canvas's content box, standing where it is written — one
    appended line, one-line undo, exactly `sink`'s manners.  It says
    nothing to the compiler, so it rewrites to a comment; the editor
    reads it off the author's text, never off this rewrite.

    **`canvas <expr>` is its own box** (Henri's `canvas discOf 5.0`,
    chopin-session.ges): the expression rewrites to a hidden
    `__canvas_<k>__ = <expr>` and the editor compiles one more
    substrate per ask, its entry pointed at the hidden name — so a
    file keeps its `substrate` *and* watches any expression beside
    it, sink's semantics where several sinks are normal.  The first
    design rewrote to `substrate = <expr>` and refused the first
    real use with a duplicate-declaration complaint about a name the
    author never wrote twice.  Numbered in reading order, the sinks'
    own rule, and the numbering is shared with `session.furniture`
    and `Workbench._load_substrate` by all three scanning the same
    way.
    """
    global _SINK, _CANVAS, _NOTES
    bare = "\n" + source
    if "\nsink " not in bare and "\ncanvas" not in bare \
            and "\nnotes " not in bare:
        return source
    import re

    if _SINK is None:
        _SINK = re.compile(r"^sink\s+(\S.*)$")
        _CANVAS = re.compile(r"^canvas(?:\s+(\S.*))?\s*$")
    if _NOTES is None:
        # **The score box's ask** (`spec/scorebox.md`), and it says
        # *nothing* to the compiler: unlike `canvas <expr>`, whose
        # expression is a picture the program must build, a `notes`
        # expression is score the box reads for itself, out of the
        # author's own text.  So it rewrites to a comment, the bare
        # `canvas` line's own manner.  What counts as an ask is
        # `scorebox.ask_of`'s to say — a program is entitled to its
        # own `notes = …`, and one has one.
        from .scorebox import ask_of as _NOTES
    out, k, b = [], 0, 0
    for line in source.splitlines():
        if _NOTES(line) is not None:
            out.append("# " + line)
            continue
        m = _SINK.match(line)
        c = _CANVAS.match(line)
        if m:
            out.append(f"__sink_{k}__ = {m.group(1)}")
            k += 1
        elif c:
            expr = c.group(1)
            # An expression that opens with `#` is a trailing comment
            # on a bare ask, not a picture.
            if expr and not expr.startswith("#"):
                out.append(f"__canvas_{b}__ = {expr}")
                b += 1
            else:
                out.append("# canvas")
        else:
            out.append(line)
    return "\n".join(out) + ("\n" if source.endswith("\n") else "")


@lru_cache(maxsize=4)
def expand(source: str, prelude: str = "") -> str:
    """Rewrite every `voices` declaration into ordinary ones.

    A program with no `voices` line is returned unchanged and unparsed, so
    nothing pays for this that does not use it.  `sink` lines are
    rewritten first (`_sinks`), here because every assembly already
    comes through this door and a second door would drift.

    `prelude`, if given, is searched for a bank's *frame* type as well as
    the program — `Stereo` lives in `synth.ges`, and a bank that produces
    it should not have to redeclare it.  The prelude is never rewritten and
    never appears in the result; it is read for its type declarations only.

    **Kept, because it is text in and text out and every assembly wants
    it.**  `audio.assemble`, `audioscore.assemble_performance` and the
    canvas each call this on the same program, several times a second in an
    editor, and for a program with four banks it is a parse per bank —
    a second of it for `examples/audio/quartet.ges`.  Four, for the reason
    `pipeline._KEEP_ANALYSED` is four.
    """
    source = _sinks(source)
    lines = source.splitlines()
    banks = _banks(lines)
    if not banks:
        if _DOTTED.search(source):
            _rewrite_dots(source, banks)        # raises, naming the bank
        if _HOLDS.search(source):
            _rewrite_holds(source, banks)       # likewise
        return source

    seen = set()
    for bank in banks:
        if bank.name in seen:
            raise VoicesError(f"two banks are both called `{bank.name}`")
        seen.add(bank.name)

    # Blanked, not removed: every line below a bank would otherwise shift,
    # and `audiospans` reports knobs by line.  It also has to happen before
    # the source can be parsed for field types at all.
    blanked = _prepare(lines, banks)

    generated: list = []
    for bank in banks:
        fields = _fields(blanked, bank.record, bank.name)
        frame = _frame(blanked, bank, prelude)
        generated += _from_midi(bank, blanked)
        generated += _builders(bank, fields)
        for i in range(bank.count):
            generated += _voice(bank, fields, i)
        generated += _sum(bank, frame)

    # `Voice` and the injections name `Assigned`, which is `music.ges`'s —
    # and a plain synth is not given `music.ges`, because nine constructors
    # and their compile time are not something a program that plays no
    # score should pay (`roadmap.md`, stage 3).  So they are emitted for a
    # program that *assigns* to a bank, which is exactly a program that
    # mentions `voices.<name>`, and such a program is assembled with the
    # music prelude by `audioperform`.
    if _DOTTED.search(source):
        generated += _voice_type(banks)
    if _HOLDS.search(source):
        generated += _holds_defs(banks)
    _refuse_collisions(blanked, generated, banks)
    return (_rewrite_holds(_rewrite_dots(blanked, banks), banks) + "\n\n"
            + "\n".join(generated) + "\n")


#: `leadMk1 : Int -> …` — a top-level signature in the generated text.
_GENERATED_SIG = re.compile(r"^([A-Za-z_][\w']*)\s*:(?![:=])", re.M)


def _refuse_collisions(source: str, generated: list, banks: list) -> None:
    """Say so when an author's name is one the expansion also defines.

    **The failure this replaces named the wrong thing entirely.**  A bank
    called `lead` generates `leadMk1`, `leadChan0f2`, `leadPayload0` and a
    dozen more into the same namespace the author writes in, so a program
    that happens to define one of them failed with

        declaration error: Duplicate type signature for 'leadMk1'

    — pointing at the author's own definition, with nothing to suggest the
    other one came from a `voices` line, and no `leadMk1` anywhere in the
    file to go and look at.

    **Renaming the generated names would not fix it**, which is why this is
    a check rather than a prefix: `leadChan0f2` and `leadFromMidi` are
    *host-facing*.  `audioschedule.py` says it outright — "`Node.chan` is
    the one name both can resolve" — and `audiomidi.FromMidi` looks its
    forwarder up by name.  Those two shapes have to keep their spelling, so
    the collision remains possible however the helpers are spelled, and the
    honest fix is to report it in terms of the declaration that caused it.
    """
    from .prelude import _defined_names

    try:
        mine = _defined_names(_module(source).items)
    except Exception:                                       # noqa: BLE001
        # An unparseable program has a better error waiting for it than
        # anything this could say about names.
        return
    for line in "\n".join(generated).split("\n"):
        found = _GENERATED_SIG.match(line)
        if found and found.group(1) in mine:
            name = found.group(1)
            whose = next((b.name for b in banks
                          if name.startswith(b.name)), banks[0].name)
            raise VoicesError(
                f"`{name}` is defined in this program and is also generated "
                f"by the `voices {whose}` declaration.\n"
                f"    A bank generates its channels, its payload builders "
                f"and its summing fold as ordinary definitions named after "
                f"it, so a program may not define one of them itself.\n"
                f"    Rename `{name}`, or rename the bank.")


#: `voices.lead` in an expression.
_DOTTED = re.compile(r"\bvoices\.([A-Za-z_]\w*)")

#: `holds.lead` — the bank's note port as a `probe` target.
_HOLDS = re.compile(r"\bholds\.([A-Za-z_]\w*)")


def _rewrite_holds(source: str, banks: list) -> str:
    """`holds.lead` → `holdsLead`, by the rule `_rewrite_dots` records."""
    known = {b.name for b in banks}

    def one(match):
        name = match.group(1)
        if name not in known:
            raise VoicesError(
                f"`holds.{name}` names no bank; this program declares "
                + (", ".join(f"`{b}`" for b in sorted(known)) or "none"))
        return "holds" + _cap(name)

    return _HOLDS.sub(one, source)


def _holds_defs(banks: list) -> list:
    """`holdsLead : Chan (List Int)` per bank — the note port a score
    listens to, as a **channel**.

    It was `holdsLead : Int = <bank index>`, an identity wearing a
    number, because `hear` took a `Port = Int`.  A channel says what
    it carries and is the identity by itself (`NChan.chan_id`), so the
    generated definition is now the thing itself rather than a token
    standing for it; `audioscore.ports_of` reads the ids back by
    forcing these.  `Chan` is a builtin type, so this stands in a
    program assembled without `music.ges` exactly as the integer did.
    """
    out = []
    for bank in banks:
        out.append(f"holds{_cap(bank.name)} : Chan (List Int)")
        out.append(f"holds{_cap(bank.name)} = chan")
        out.append("")
    return out


def _rewrite_dots(source: str, banks: list) -> str:
    """`voices.lead` → `voicesLead`.

    Textual, and deliberately so.  `.` is projection in gestate — `x.0`,
    `x.field`, resolved from the base's type — so `voices.lead` would parse
    as a projection out of a variable called `voices`, which is not what it
    means and would need `voices` to be a record with a *polymorphic* field.
    Rewriting here keeps the spelling without asking the parser to grow a
    case, and it is the same source-to-source move the rest of this module
    makes.

    A mention inside a comment is rewritten too.  Harmless: the comment then
    reads `voicesLead`, which is the name it becomes.

    A name that is not a declared bank is refused **here**, where the
    spelling the author wrote is still visible.  Left to the type checker
    it would surface as `Unknown global 'voicesNothing'` — a name nobody
    typed, from a rewrite they did not know had happened.
    """
    known = {b.name for b in banks}

    def one(match):
        name = match.group(1)
        if name not in known:
            raise VoicesError(
                f"`voices.{name}` names no bank; this program declares "
                + (", ".join(f"`{b}`" for b in sorted(known)) or "none"))
        return "voices" + _cap(name)

    return _DOTTED.sub(one, source)


def blanked(source: str) -> str:
    """`source` with its `voices` declarations blanked out.

    For any reader that needs to *parse* the author's text rather than run
    it: `voices lead 6 reed : Sig Float` is not gestate syntax, which is the
    whole point of expanding it, and a parser meets it first.  Blanked
    rather than removed so line numbers do not move.

    **`sink` and `canvas` lines are rewritten first**, because they are
    the same kind of word: author text a parser meets before any
    assembly.  Found the hard way twice in one day — a `canvas` line
    took lantern's knobs to "no parameters" (the spans placer parses
    through here), and the probe showed top-level `sink` had been
    breaking the same placement since it shipped, unnoticed because
    every sinked example so far had no knobs to lose.

    The payload is deliberately *not* resolved here — that reads the parsed
    program, and this is what makes the program parseable.  A caller that
    wants prepared banks asks `banks_of`.
    """
    source = _sinks(source)
    lines = source.splitlines()
    found = _banks(lines)
    for bank in found:
        _find_voice(bank, lines)
    return _blank(lines, found)


def banks_of(source: str) -> list:
    """The banks a program declares, without expanding it.

    What a scheduler needs: the name of each bank, how many voices it has,
    and the channel names of each voice's parameters — which is how a note
    reaches the engine.

    Prepared exactly as `expand` prepares them, because a `Bank` whose
    payload is still blank is one every reader would have to fill in for
    itself — and the schedule, the editor's bank rows and the expansion
    have to agree about what a voice's channels are.

    **Fresh `Bank`s off a cached reading.**  `_prepare` *parses* the
    program once per bank to read each payload off its voice, and this is
    asked several times a second by readers that know nothing of each
    other — `channels_of` alone asks once per bank.  A `Bank` is mutable
    (`_prepare` fills its `record` in), so what is kept is the reading and
    what is handed out is a copy: a caller that writes to one cannot reach
    the next caller's.
    """
    from dataclasses import replace

    return [replace(b) for b in _prepared(source)]


@lru_cache(maxsize=4)
def _prepared(source: str) -> tuple:
    """`banks_of`'s answer, kept.  See there for why it is copied out."""
    # `sink` lines rewritten first, as `expand` rewrites them: this
    # door takes the author's raw text, and a `sink` reaching the
    # parser is not gestate syntax — the start refused whole programs
    # over the line the probing tool exists to make free.
    source = _sinks(source)
    lines = source.splitlines()
    banks = _banks(lines)
    _prepare(lines, banks)
    return tuple(banks)


def channels_of(source: str, bank: Bank) -> list:
    """`[[channel name per field] per voice]` for one bank.

    The layout a scheduler writes into: `channels_of(...)[3][0]` is voice
    3's first field, and a `Schedule` keyed by those names drives both the
    interpreter and the engine.
    """
    fields = _fields(_blank(_sinks(source).splitlines(),
                            banks_of(source)),
                     bank.record, bank.name)
    return [[f"{bank.name}Chan{i}f{j}"
             for j in range(len(TIMING) + len(fields))]
            for i in range(bank.count)]
