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


def note_bank(source: str, graph, rate: int):
    """`(voices, table)` for the bank a keyboard plays, or `None`.

    The **first declared bank**, which is this exporter's answer to
    "which bank listens" — live, that is the environment's switch; a
    plugin has no environment, and the first bank is the author's own
    ordering.  `voices` is `audioalloc`'s channel layout resolved to
    control-slot indices; `table` is the program's `FromMIDI` instance
    run through the G-machine at export time, 128 keys × `VEL_LEVELS`
    velocities on channel 0 — the same evaluations `audiomidi.FromMidi`
    makes per key press live, made once here instead.  A bank with no
    instance gets `None`, and the shell uses the structural
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
        return None
    bank = banks[0]
    slot_of = {n.chan: i for i, n in enumerate(graph.control_sources())}
    voices = [[slot_of[c] for c in voice]
              for voice in channels_of(source, bank)]

    assembled = (assemble_performance(source, "", rate)
                 if has_score(source) else assemble(source, rate))
    fm = FromMidi(_compile(assembled), [b.name for b in banks])
    if not fm.offers(bank.name):
        return voices, None

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
                    struct.unpack("<q", struct.pack("<d", float(value)))[0]
                    if kind == "Float" else int(value))
    return voices, (ok, data, fields)


def _bank_rs(bank) -> str:
    """The `Bank` half of `descriptor.rs`."""
    if bank is None:
        return "pub static BANK: Option<&Bank> = None;\n"
    voices, table = bank
    out = []
    for i, voice in enumerate(voices):
        out.append(f"static VOICE{i}: [usize; {len(voice)}] = "
                   f"{voice!r};\n")
    rows = ", ".join(f"&VOICE{i}" for i in range(len(voices)))
    out.append(f"static VOICES: [&'static [usize]; {len(voices)}] = "
               f"[{rows}];\n")
    if table is None:
        out.append("pub static BANK: Option<&Bank> = Some(&THE_BANK);\n"
                   "static THE_BANK: Bank = "
                   "Bank { voices: &VOICES, table: None };\n")
        return "".join(out)
    ok, data, fields = table
    flags = ", ".join("true" if b else "false" for b in ok)
    cells = ", ".join(str(v) for v in data)
    out.append(f"static NOTE_OK: [bool; {len(ok)}] = [{flags}];\n")
    out.append(f"static NOTE_DATA: [i64; {len(data)}] = [{cells}];\n")
    out.append(f"static TABLE: NoteTable = NoteTable {{ levels: "
               f"{VEL_LEVELS}, fields: {fields}, ok: &NOTE_OK, "
               f"data: &NOTE_DATA }};\n")
    out.append("pub static BANK: Option<&Bank> = Some(&THE_BANK);\n"
               "static THE_BANK: Bank = "
               "Bank { voices: &VOICES, table: Some(&TABLE) };\n")
    return "".join(out)


def descriptor_rs(graph, *, id_: str, name: str, version: str,
                  rate: int, knobs: frozenset, bank=None) -> str:
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
    # `Bank` always: the bank-less descriptor still *names* the type in
    # its `None`.
    used = ["Bank", "Control", "Descriptor"]
    if controls:
        used.append("Kind")
    if bank is not None and bank[1] is not None:
        used.append("NoteTable")
    kinds = "use super::{" + ", ".join(sorted(used)) + "};"
    return (f"// Written by `python -m gestate.export` — regenerated per "
            f"export, never edited.\n"
            f"{kinds}\n\n"
            f"{_bank_rs(bank)}\n"
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


def archive(graph, directory) -> Path:
    """`libgraph.a` — the graph's code as something a linker takes.

    The same IR `audiollvm.build` turns into the live engine's shared
    object, compiled to an object file instead: `clang -c` then `ar`.
    One archive per export, in a directory the export owns, because
    `build.rs` is pointed at the *directory* and two graphs in one
    would be a coin toss.
    """
    from .audiollvm import emit

    directory = Path(directory)
    ll = directory / "graph.ll"
    obj = directory / "graph.o"
    ll.write_text(emit(graph))
    subprocess.run(["clang", "-O2", "-c", "-fPIC", str(ll),
                    "-o", str(obj)], check=True, capture_output=True)
    lib = directory / "libgraph.a"
    subprocess.run(["ar", "rcs", str(lib), str(obj)],
                   check=True, capture_output=True)
    return lib


def export_clap(source: str, out: Path, *, rate: int, name: str,
                version: str = "0.1.0", shell: Path = SHELL) -> Path:
    """One `.ges` in, one `.clap` out."""
    import shutil
    import tempfile

    from .audioperform import graph_of

    if shutil.which("clang") is None:
        raise ExportError("no clang to build the graph with")
    if shutil.which("cargo") is None:
        raise ExportError("no cargo to build the shell with — the CLAP "
                          "shell is Rust (`shell/clap/`)")

    graph = graph_of(source, "", rate=rate)
    for node in graph.control_sources():
        if node.type_ not in ("Float", "Int", "Gate", "Key"):
            # A slot is one i64 and the shell reinterprets it the way
            # `Host.set_control` does; a channel of any other shape is
            # a fact this generator would silently mangle.
            raise ExportError(
                f"channel `{node.chan}` carries `{node.type_}`, which "
                f"does not fit a control slot")

    banked = bank_channels(source)
    knobs = frozenset(n.chan for n in graph.control_sources()
                      if n.chan not in banked)
    bank = note_bank(source, graph, rate)
    with tempfile.TemporaryDirectory() as d:
        archive(graph, d)
        (shell / "src" / "descriptor.rs").write_text(descriptor_rs(
            graph, id_=f"org.gestate.{name}", name=name,
            version=version, rate=rate, knobs=knobs, bank=bank))
        env = dict(**__import__("os").environ, GESTATE_GRAPH_DIR=d)
        done = subprocess.run(
            ["cargo", "build", "--release", "--features", "engine"],
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
    ap.add_argument("--rate", type=int, default=48000,
                    help="the sample rate the graph is compiled at; the "
                         "plugin refuses activation at any other")
    args = ap.parse_args(argv)

    path = Path(args.file)
    name = path.stem
    out = Path(args.out) if args.out else Path(f"{name}.clap")
    try:
        made = export_clap(path.read_text(), out, rate=args.rate,
                           name=name)
    except ExportError as exc:
        print(f"gestate: {exc}")
        return 1
    print(f"wrote {made}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
