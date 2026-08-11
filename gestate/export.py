"""`python -m gestate.export` — the instrument leaves the workshop.

    python -m gestate.export examples/audio/blip.ges -o blip.clap

`spec/export.md` is the design; this is its generator.  A `.clap` is a
shared object a DAW probes for `clap_entry`, and this builds one from a
`.ges` file in three moves:

1. the graph's IR (`audiollvm.emit`) becomes a **static archive** —
   the same code the live engine runs, linked instead of loaded;
2. a `descriptor.rs` telling the shell what only the compiler knows:
   the rate the graph is truthful at, its channel count, its state
   width, and the control table in buffer order;
3. `cargo build --features engine` in `shell/clap/`, and the resulting
   library is the plugin, renamed.

**No state image travels.**  The engine's state starts as zeroes —
the generated code's first-instant branch seeds every `init` itself —
so the descriptor's `state_bytes` is the whole memory story, computed
the way `audiolive.Engine.compile` computes it.
"""

from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path


class ExportError(Exception):
    pass


#: The shell crate, relative to this package's repository.
SHELL = Path(__file__).resolve().parent.parent / "shell" / "clap"


def _rust_str(s: str) -> str:
    """A Rust string literal.  `json.dumps` escapes to a subset Rust
    accepts (`\\"`, `\\uXXXX`), so the two agree on every character."""
    return json.dumps(s)


def _init_bits(node) -> int:
    """The control slot's value before anyone moves it — the program's
    own declared default, reinterpreted the way `Host.set_control` and
    `audiollvm.pack_control` reinterpret: a Float is its bit pattern in
    the i64 slot, everything else is the integer."""
    if node.type_ == "Float":
        return struct.unpack("<q", struct.pack("<d", float(node.init)))[0]
    return int(node.init)


def bank_channels(source: str) -> frozenset:
    """Every control channel the `voices` expansion generated.

    These carry notes — a bank's gates, offs and payload fields — and a
    DAW must never draw a knob for one: automation writing into
    `keysChan0f2` is a note nobody played.  Everything *else* a program
    declares as a channel is a knob by that program's own choice, which
    is the rule the editors already live by from the other side.
    """
    from .audiovoices import banks_of, channels_of

    names: set = set()
    for bank in banks_of(source):
        for voice in channels_of(source, bank):
            names.update(voice)
    return frozenset(names)


def _range_of(node) -> tuple:
    """`(min, max)` for a knob's parameter — the knob convention.

    A knob is `0 .. 100` at `Int` and `0 .. 1.0` at `Float`, which is
    what the dials mean everywhere else in this project.  A default
    outside its own convention stretches the top to include it rather
    than sitting outside its own range.  The day the language grows a
    declared range, this function is what it deletes.
    """
    if node.type_ == "Float":
        return 0.0, max(1.0, float(node.init))
    return 0.0, float(max(100, int(node.init)))


#: `noteOn`'s velocity axis, tabled: 32 levels, each evaluated at the
#: top of its bucket (`level·4 + 3`) so full velocity is exact at 127.
#: A stated quantisation — 32 loudnesses per key — until somebody hears
#: it, which for most instances (velocity-linear or velocity-blind) is
#: never.
VEL_LEVELS = 32


def note_banks(source: str, graph, rate: int) -> list:
    """`[(name, voices, table)]` for **every** bank, in declaration
    order — the order that gives the routing matrix its default
    diagonal, `audiomidi.by_midi_channel`'s own rule: MIDI channel *n*
    plays bank *n*.

    Per bank, `voices` is `audioalloc`'s channel layout resolved to
    control-slot indices, and `table` is the program's `FromMIDI`
    instance run through the G-machine at export time, 128 keys ×
    `VEL_LEVELS` velocities — the same evaluations `audiomidi.FromMidi`
    makes per key press live, made once here.  (Channel 0 to the
    instance: a plugin routes by the matrix, so an instance's own
    channel-based declining is superseded by it.)  A bank with no
    instance gets `None` and the shell uses the structural
    `(key, velocity)` payload the live path defaults to.
    """
    from .audio import assemble
    from .audiomidi import FromMidi
    from .audioperform import has_score
    from .audioscore import assemble_performance
    from .audiovoices import banks_of, channels_of
    from .pipeline import compile as _compile

    banks = banks_of(source)
    if not banks:
        return []
    slot_of = {n.chan: i for i, n in enumerate(graph.control_sources())}
    assembled = (assemble_performance(source, "", rate)
                 if has_score(source) else assemble(source, rate))
    fm = FromMidi(_compile(assembled), [b.name for b in banks])

    out = []
    for bank in banks:
        voices = [[slot_of[c] for c in voice]
                  for voice in channels_of(source, bank)]
        if not fm.offers(bank.name):
            out.append((bank.name, voices, None))
            continue
        fields = len(voices[0]) - 2
        kinds = [graph.control_sources()[s].type_ for s in voices[0][2:]]
        ok: list = []
        data: list = []
        for key in range(128):
            for level in range(VEL_LEVELS):
                payload = fm.payload_for(bank.name, 0, key,
                                         min(127, level * 4 + 3))
                if payload is None or len(payload) != fields:
                    ok.append(False)
                    data.extend([0] * fields)
                    continue
                ok.append(True)
                for value, kind in zip(payload, kinds):
                    data.append(
                        struct.unpack("<q",
                                      struct.pack("<d", float(value)))[0]
                        if kind == "Float" else int(value))
        out.append((bank.name, voices, (ok, data, fields)))
    return out


def score_events(source: str, graph, rate: int):
    """The piece's own events in beats, for the shell's cursor —
    `spec/dynamicscore.md` stage one's descriptor half.

    `[(tick, key, bank_index, is_off, payload_bits)]` in the
    performance's one true order, or `None` when the program has no
    score or an unfolding one.  The order and the identities are
    `timed_events`' own, taken at the identity tempo — 60 bpm at
    `TICKS_PER_BEAT` samples a second makes `samples_of` the identity
    on ticks, so the shared sort is reused rather than respelled.
    An unfolding score is the honest discard it has always been in an
    export: until the G-machine travels (`spec/crust.md`), the plugin
    is the instrument without its piece.
    """
    from .audioperform import has_score
    from .audioscore import (ScoreError, _flatten, perform_voices,
                             timed_events)
    from .audiovoices import banks_of, channels_of
    from .midi import TICKS_PER_BEAT

    if not has_score(source):
        return None
    try:
        _bpm, events = perform_voices(source, "", rate)
    except ScoreError:
        return None
    banks = banks_of(source)
    index = {b.name: i for i, b in enumerate(banks)}
    controls = graph.control_sources()
    slot_of = {n.chan: i for i, n in enumerate(controls)}
    kinds = {}
    for b in banks:
        first = channels_of(source, b)[0]
        kinds[b.name] = [controls[slot_of[c]].type_ for c in first[2:]]

    out = []
    for tick, _order, key, bank, payload, is_off in timed_events(
            events, 60, TICKS_PER_BEAT):
        bits: tuple = ()
        if not is_off:
            bits = tuple(
                struct.unpack("<q", struct.pack("<d", float(v)))[0]
                if kind == "Float" else int(v)
                for v, kind in zip(_flatten(payload), kinds[bank]))
        out.append((tick, key, index[bank], is_off, bits))
    return out


def program_of(source: str, rate: int):
    """The piece as a **program**, for a score no event list can hold.

    `spec/dynamicscore.md` stage two, abroad.  `score_events` above
    returns `None` for an unfolding score because there is no finite
    list to write; this returns what to send instead — the compiled
    G-machine program, the entry to force it at, and the constructor
    tags the stream decodes cells with.

    Tags travel because a tag is a *position* in the program's own
    constructor table.  The shell cannot derive one, and a shell that
    guessed would decode a cue as whatever happened to share its
    number.

    `None` when the program cannot cross — a Datafun-shaped or
    otherwise non-core definition reachable from `liveMain` — which is
    the same honest refusal `live_native` makes at home, and leaves the
    export to bake or to discard as before.
    """
    from .audioperform import has_score
    from .audioscore import ScoreError, stream_root, unfolding_names
    from .audiovoices import banks_of
    from .crust import CrustError, serialize

    if not has_score(source) or not unfolding_names(source):
        return None

    try:
        _tempo, state, _root, by_tag = stream_root(source, "", rate, 0,
                                                   live=True)
        text = serialize(state, "liveMain")
    except (CrustError, ScoreError, KeyError):
        return None

    # `by_tag` is tag → *bank name*; the shell wants tag → bank index,
    # because the wire's third word is a tag and `Bank` is positional.
    index = {b.name: i for i, b in enumerate(banks_of(source))}
    voices = [(tag, index[name]) for tag, name in by_tag.items()
              if name in index]
    # The note ports: `hear holds.keys` asks by channel id, and the
    # shell answers with what that bank is holding.
    from .audioscore import ports_of
    holds = [(chan, index[name])
             for chan, name in ports_of(source, state).items()
             if name in index]
    cons = state.cons
    return {
        "text": text,
        "entry": "liveMain",
        "seed": 0,
        "cons": cons["Cons"].tag,
        "nil": cons["Nil"].tag,
        "cue_ev": cons["CueEv"].tag,
        "cue_ask": cons["CueAsk"].tag,
        "cue_end": cons["CueEnd"].tag,
        "voices": sorted(voices),
        "holds": sorted(holds),
    }


def _program_rs(program) -> str:
    """The `PROGRAM` fourth of `descriptor.rs`."""
    if program is None:
        # Not even the `None`: without `dynscore` the crate has no
        # `Program` type to name, and `engine.rs` supplies the empty
        # case itself.
        return ""
    voices = ", ".join(f"({t}, {b})" for t, b in program["voices"])
    holds = ", ".join(f"({c}, {b})" for c, b in program["holds"])
    return (
        f"static VOICE_BANKS: &[(i64, usize)] = &[{voices}];\n"
        f"static HOLDS: &[(i64, usize)] = &[{holds}];\n"
        "pub static PROGRAM: Option<Program> = Some(Program {\n"
        f"    text: {_rust_str(program['text'])},\n"
        f"    entry: {_rust_str(program['entry'])},\n"
        f"    seed: {program['seed']},\n"
        f"    cons_tag: {program['cons']},\n"
        f"    nil_tag: {program['nil']},\n"
        f"    cue_ev_tag: {program['cue_ev']},\n"
        f"    cue_ask_tag: {program['cue_ask']},\n"
        f"    cue_end_tag: {program['cue_end']},\n"
        "    voice_banks: VOICE_BANKS,\n"
        "    holds: HOLDS,\n"
        "});\n")


def scored_banks(source: str) -> list:
    """Per bank, whether the **score** writes it.

    `audioscore.assigned_banks` by parsed mention, so it answers for an
    unfolding piece too — which is the case that needs it, since a
    dynamic score has no baked schedule to read the answer off.

    What it is for: a bank the piece plays must not also be the
    keyboard's by default.  That is the **two-bank law** the listening
    pieces are built on — an arpeggiator cannot listen to the bank it
    writes — and routing MIDI into a scored bank fills the voices the
    piece needs, so the piece goes quiet and the player hears their own
    notes instead.
    """
    from .audioscore import assigned_banks
    from .audiovoices import banks_of

    try:
        scored = assigned_banks(source)
    except Exception:
        return [False] * len(banks_of(source))
    return [b.name in scored for b in banks_of(source)]


def _score_rs(score, bpm: float) -> str:
    """The `SCORE` third of `descriptor.rs`."""
    from .midi import TICKS_PER_BEAT

    out = []
    rows = []
    payloads: dict = {}
    for tick, key, bank, is_off, bits in (score or []):
        ref = "&[]"
        if bits:
            if bits not in payloads:
                payloads[bits] = f"SP{len(payloads)}"
                cells = ", ".join(str(v) for v in bits)
                out.append(f"static {payloads[bits]}: [i64; {len(bits)}] "
                           f"= [{cells}];\n")
            ref = f"&{payloads[bits]}"
        rows.append(f"    ScoreEvent {{ tick: {tick}, key: {key}, "
                    f"bank: {bank}, "
                    f"is_off: {'true' if is_off else 'false'}, "
                    f"payload: {ref} }},\n")
    out.append("pub static SCORE: &[ScoreEvent] = &[\n"
               + "".join(rows) + "];\n")
    out.append(f"pub static SCORE_TPB: i64 = {TICKS_PER_BEAT};\n")
    out.append(f"pub static SCORE_BPM: f64 = {bpm!r};\n")
    return "".join(out)


def _banks_rs(banks: list) -> str:
    """The `BANKS` half of `descriptor.rs`."""
    if not banks:
        return "pub static BANKS: &[Bank] = &[];\n"
    out = []
    entries = []
    for b, (name, voices, table) in enumerate(banks):
        for i, voice in enumerate(voices):
            out.append(f"static B{b}V{i}: [usize; {len(voice)}] = "
                       f"{voice!r};\n")
        rows = ", ".join(f"&B{b}V{i}" for i in range(len(voices)))
        out.append(f"static B{b}VOICES: [&'static [usize]; "
                   f"{len(voices)}] = [{rows}];\n")
        table_ref = "None"
        if table is not None:
            ok, data, fields = table
            flags = ", ".join("true" if x else "false" for x in ok)
            cells = ", ".join(str(v) for v in data)
            out.append(f"static B{b}OK: [bool; {len(ok)}] = [{flags}];\n")
            out.append(f"static B{b}DATA: [i64; {len(data)}] = "
                       f"[{cells}];\n")
            out.append(f"static B{b}TABLE: NoteTable = NoteTable {{ "
                       f"levels: {VEL_LEVELS}, fields: {fields}, "
                       f"ok: &B{b}OK, data: &B{b}DATA }};\n")
            table_ref = f"Some(&B{b}TABLE)"
        entries.append(f"    Bank {{ name: {_rust_str(name)}, "
                       f"voices: &B{b}VOICES, table: {table_ref} }},\n")
    out.append("pub static BANKS: &[Bank] = &[\n"
               + "".join(entries) + "];\n")
    return "".join(out)


def _bools(flags) -> str:
    return "[" + ", ".join("true" if f else "false" for f in flags) + "]"


def descriptor_rs(graph, *, id_: str, name: str, version: str,
                  rate: int, knobs: frozenset, bank=None, program=None,
                  scored=None,
                  graphs=None, beat=None, score=None,
                  bpm: float = 120.0) -> str:
    """The Rust the shell includes — everything only the compiler knows."""
    from .audiollvm import _slots

    state_bytes = 8 * (1 + sum(_slots(graph, n) for n in graph.nodes))
    controls = graph.control_sources()
    rows = []
    for n in controls:
        lo, hi = _range_of(n) if n.chan in knobs else (0.0, 0.0)
        rows.append(
            f"    Control {{ chan: {_rust_str(n.chan)}, "
            f"kind: Kind::{'Float' if n.type_ == 'Float' else 'Int'}, "
            f"init_bits: {_init_bits(n)}, "
            f"knob: {'true' if n.chan in knobs else 'false'}, "
            f"min: {lo!r}, max: {hi!r} }},\n")
    # `Bank`, `RateCase` and `ScoreEvent` always: the bank-less
    # descriptor still *names* the types in its empty slices.
    used = ["Bank", "Control", "Descriptor", "RateCase", "ScoreEvent"]
    if program is not None:
        used.append("Program")
    if controls:
        used.append("Kind")
    if any(table is not None for _n, _v, table in (bank or [])):
        used.append("NoteTable")
    kinds = "use super::{" + ", ".join(sorted(used)) + "};"
    return (f"// Written by `python -m gestate.export` — regenerated per "
            f"export, never edited.\n"
            f"{kinds}\n\n"
            f"{_rates_rs(graphs if graphs is not None else {rate: graph})}\n"
            f"{_banks_rs(bank or [])}\n"
            f"pub static SCORED: &[bool] = &{_bools(scored or [])};\n"
            f"{_score_rs(score, bpm)}\n"
            f"{_program_rs(program)}\n"
            f"pub static BEAT_SLOTS: Option<(usize, usize, usize)> = "
            f"{'Some(' + repr(tuple(beat)) + ')' if beat else 'None'};\n\n"
            f"pub static DESCRIPTOR: Descriptor = Descriptor {{\n"
            f"    id: {_rust_str(id_)},\n"
            f"    name: {_rust_str(name)},\n"
            f"    version: {_rust_str(version)},\n"
            f"    rate: {rate},\n"
            f"    channels: {graph.channels()},\n"
            f"    state_bytes: {state_bytes},\n"
            f"    controls: &CONTROLS,\n"
            f"}};\n\n"
            f"static CONTROLS: [Control; {len(controls)}] = "
            f"[\n{''.join(rows)}];\n")


#: The entry points one compiled graph exports, longest first so the
#: rename never eats a longer name's prefix.
_ENTRIES = ("render_block_mix_f32", "render_block_f32", "render_block")


def archive(graphs: dict, directory) -> Path:
    """`libgraph.a` — every rate's graph, coexisting in one archive.

    The same IR `audiollvm.build` turns into the live engine's shared
    object, one object per rate: the entry symbols are renamed with the
    rate as a suffix (the `.ll` is text, and the rename is three
    ordered replaces), and `objcopy` then localises everything *else*
    in each object — two graphs share every internal helper name, and
    keeping only the renamed entries global is what lets them link
    side by side.
    """
    import re

    from .audiollvm import emit

    directory = Path(directory)
    objs = []
    for rate, graph in graphs.items():
        text = emit(graph)
        for name in _ENTRIES:
            # `\b`: `@render_block` must not match inside
            # `@render_block_f32` — `_` is a word character, so the
            # boundary holds exactly where the plain name ends.
            text = re.sub(rf"@{name}\b", f"@{name}_{rate}", text)
        ll = directory / f"graph_{rate}.ll"
        obj = directory / f"graph_{rate}.o"
        ll.write_text(text)
        subprocess.run(["clang", "-O2", "-c", "-fPIC", str(ll),
                        "-o", str(obj)], check=True, capture_output=True)
        keep = [arg for name in _ENTRIES
                for arg in ("-G", f"{name}_{rate}")]
        subprocess.run(["objcopy", *keep, str(obj)],
                       check=True, capture_output=True)
        objs.append(str(obj))
    lib = directory / "libgraph.a"
    subprocess.run(["ar", "rcs", str(lib), *objs],
                   check=True, capture_output=True)
    return lib


def _rates_rs(graphs: dict) -> str:
    """The `RATES` half of `descriptor.rs` — one case per compiled rate."""
    from .audiollvm import _slots

    externs = []
    cases = []
    for rate, graph in graphs.items():
        state = 8 * (1 + sum(_slots(graph, n) for n in graph.nodes))
        externs.append(
            f"    fn render_block_f32_{rate}(state: *mut u8, "
            f"out: *mut f32, frames: i64, control: *const i64);\n")
        cases.append(f"    RateCase {{ rate: {rate}, "
                     f"state_bytes: {state}, "
                     f"render: render_block_f32_{rate} }},\n")
    return ("extern \"C\" {\n" + "".join(externs) + "}\n\n"
            "pub static RATES: &[RateCase] = &[\n"
            + "".join(cases) + "];\n")


#: What a plugin is honest at unless told otherwise — the two rates
#: sessions actually run at.
DEFAULT_RATES = (44100, 48000)

#: The channels the host clock rides in on.  Spelled here and *only*
#: here: the shell learns their slots from the descriptor
#: (`BEAT_SLOTS`), never from these names — the context contract's
#: answer to the `tempoChan` convention this replaces.
_BEAT_CHANS = ("beatBaseChan", "beatBpsChan", "beatTickChan")


def _bpm_of(source: str) -> float:
    """The program's own tempo as a number, for the free-running default.

    A `bpm = N` literal, read textually — the common case, and the
    fallback of 120 costs a program with a computed `bpm` only its
    tempo *before a transport speaks*, which no DAW leaves long."""
    import re

    found = re.search(r"^bpm\s*=\s*(\d+)", source, re.M)
    return float(found.group(1)) if found else 120.0


def host_clock(source: str) -> str:
    """`beat` and `beatRate`, fed by whoever is hosting.

    The renderer's-own clock for an exported plugin
    (`spec/substrate.md`, the context contract): three channels carry
    a *line* — the beat at some recent block start, the beats per
    second, and the sample that anchor was taken at — and `beat` is
    that line evaluated at `ticks`, audio-rate smooth however coarsely
    the host updates it.  `beatRate` is the same middle channel bare:
    how fast the piece is going, in beats a second.

    Untouched channels hold the program's *own* tempo (`bpm`, or 120),
    so a free-running host plays the piece at its declared pace — the
    program is its own conductor exactly until a transport speaks.
    """
    bps = _bpm_of(source) / 60.0
    return (f"\nbeatBaseChan : Chan Float\nbeatBaseChan = chan\n"
            f"\nbeatBpsChan : Chan Float\nbeatBpsChan = chan\n"
            f"\nbeatTickChan : Chan Int\nbeatTickChan = chan\n"
            f"\nbeatRate : Sig Float\n"
            f"beatRate = {bps!r} ::: mkSig (wait beatBpsChan)\n"
            f"\nbeat : Sig Float\n"
            f"beat = (0.0 ::: mkSig (wait beatBaseChan))\n"
            f"     + beatRate * (map toFloat ticks\n"
            f"         - map toFloat (0 ::: mkSig (wait beatTickChan)))\n"
            f"       * !(1.0 / sampleRate)\n")


def host_graph(source: str, rate: int):
    """The graph, assembled with the host-fed clock in `beat`'s place."""
    from .audio import assemble
    from .audioextract import extract_analysis
    from .audioperform import has_score
    from .audioscore import assemble_performance
    from .pipeline import analyse

    clock = host_clock(source)
    text = (assemble_performance(source, "", rate, clock_text=clock)
            if has_score(source) else
            assemble(source, rate, clock_text=clock))
    return extract_analysis(analyse(text), rate=rate)


def beat_slots(graph):
    """`(base, bps, tick)` slot indices, or `None` when the program
    never reaches `beat` — reachability prunes the channels, and a
    plugin with no use for a clock carries none."""
    slot_of = {n.chan: i for i, n in enumerate(graph.control_sources())}
    try:
        return tuple(slot_of[c] for c in _BEAT_CHANS)
    except KeyError:
        return None


def export_clap(source: str, out: Path, *, rate=None, name: str,
                version: str = "0.1.0", shell: Path = SHELL,
                gui: bool = False) -> Path:
    """One `.ges` in, one `.clap` out.

    `rate` may be one rate or several; the default is both of
    `DEFAULT_RATES`.  Each is a whole compiled graph — `sampleRate` is
    folded through the program — and `activate` picks the case the
    host names, still refusing the rates the plugin would lie at.

    `gui` adds the plugin's own window (`spec/panel.md`) — the knob
    and note-routing panels drawn from the descriptor this function
    just wrote.  It is **off by default and stays that way**: without
    it the shell has no dependencies at all, which is the property
    `shell/README.md` is built around, and a plugin is perfectly
    playable through the host's generic parameter view.
    """
    import shutil
    import tempfile

    from .audioperform import graph_of

    if shutil.which("clang") is None:
        raise ExportError("no clang to build the graph with")
    if shutil.which("cargo") is None:
        raise ExportError("no cargo to build the shell with — the CLAP "
                          "shell is Rust (`shell/clap/`)")

    rates = (list(DEFAULT_RATES) if rate is None
             else [rate] if isinstance(rate, int) else list(rate))
    graphs = {r: host_graph(source, r) for r in rates}
    primary = rates[0]
    graph = graphs[primary]
    for node in graph.control_sources():
        if node.type_ not in ("Float", "Int", "Gate", "Key"):
            # A slot is one i64 and the shell reinterprets it the way
            # `Host.set_control` does; a channel of any other shape is
            # a fact this generator would silently mangle.
            raise ExportError(
                f"channel `{node.chan}` carries `{node.type_}`, which "
                f"does not fit a control slot")
    # The slot table must be one table: rate only changes folded
    # constants, so the channel order must agree across the graphs —
    # asserted, because everything downstream indexes by it.
    order = [n.chan for n in graph.control_sources()]
    for r, g in graphs.items():
        if [n.chan for n in g.control_sources()] != order:
            raise ExportError(f"the graph at {r} Hz orders its channels "
                              f"differently — export cannot share slots")

    banked = bank_channels(source)
    knobs = frozenset(n.chan for n in graph.control_sources()
                      if n.chan not in banked
                      and n.chan not in _BEAT_CHANS)
    bank = note_banks(source, graph, primary)
    beat = beat_slots(graph)
    score = score_events(source, graph, primary)
    # **The piece, when no list can hold it.**  `score_events` returns
    # `None` for an unfolding score; this is what travels instead — the
    # compiled program, which the shell forces as it plays
    # (`spec/dynamicscore.md` stage two, abroad).
    program = program_of(source, primary) if score is None else None
    with tempfile.TemporaryDirectory() as d:
        archive(graphs, d)
        (shell / "src" / "descriptor.rs").write_text(descriptor_rs(
            graph, id_=f"org.gestate.{name}", name=name,
            version=version, rate=primary, knobs=knobs, bank=bank,
            graphs=graphs, beat=beat, score=score, program=program,
            scored=scored_banks(source),
            bpm=_bpm_of(source)))
        env = dict(**__import__("os").environ, GESTATE_GRAPH_DIR=d)
        # `--target-dir` pins the artifact under the shell whether or
        # not the crate builds inside the workspace — the workspace
        # root's `target/` is where cargo would otherwise put it.
        features = ["engine"]
        if gui:
            features.append("gui")
        if program is not None:
            features.append("dynscore")
        features = ",".join(features)
        done = subprocess.run(
            ["cargo", "build", "--release", "--features", features,
             "--target-dir", str(shell / "target")],
            cwd=shell, env=env, capture_output=True, text=True)
        if done.returncode != 0:
            raise ExportError("the shell did not build:\n" + done.stderr)
        built = shell / "target" / "release" / "libgestate_clap.so"
        out = Path(out)
        shutil.copyfile(built, out)
    return out


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.export",
        description="Export a synth as a CLAP plugin.")
    ap.add_argument("file")
    ap.add_argument("-o", "--out", default=None,
                    help="output path (default: <name>.clap)")
    ap.add_argument("--rate", type=int, action="append", default=None,
                    help="a sample rate to compile the graph at; may "
                         "repeat.  Default: 44100 and 48000.  The "
                         "plugin refuses activation at any rate it "
                         "does not carry")
    ap.add_argument("--gui", action="store_true",
                    help="build the plugin's own window as well "
                         "(spec/panel.md): knobs and the note-routing "
                         "panels, drawn from this plugin's descriptor. "
                         "Costs the shell its zero-dependency build")
    args = ap.parse_args(argv)

    path = Path(args.file)
    name = path.stem
    out = Path(args.out) if args.out else Path(f"{name}.clap")
    try:
        made = export_clap(path.read_text(), out, rate=args.rate,
                           name=name, gui=args.gui)
    except ExportError as exc:
        print(f"gestate: {exc}")
        return 1
    print(f"wrote {made}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
