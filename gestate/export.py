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


def descriptor_rs(graph, *, id_: str, name: str, version: str,
                  rate: int) -> str:
    """The Rust the shell includes — everything only the compiler knows."""
    from .audiollvm import _slots

    state_bytes = 8 * (1 + sum(_slots(graph, n) for n in graph.nodes))
    controls = graph.control_sources()
    rows = "".join(
        f"    Control {{ chan: {_rust_str(n.chan)}, "
        f"kind: Kind::{'Float' if n.type_ == 'Float' else 'Int'}, "
        f"init_bits: {_init_bits(n)} }},\n"
        for n in controls)
    kinds = "use super::{Control, Descriptor, Kind};" if controls else \
            "use super::{Control, Descriptor};"
    return (f"// Written by `python -m gestate.export` — regenerated per "
            f"export, never edited.\n"
            f"{kinds}\n\n"
            f"pub static DESCRIPTOR: Descriptor = Descriptor {{\n"
            f"    id: {_rust_str(id_)},\n"
            f"    name: {_rust_str(name)},\n"
            f"    version: {_rust_str(version)},\n"
            f"    rate: {rate},\n"
            f"    channels: {graph.channels()},\n"
            f"    state_bytes: {state_bytes},\n"
            f"    controls: &CONTROLS,\n"
            f"}};\n\n"
            f"static CONTROLS: [Control; {len(controls)}] = [\n{rows}];\n")


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

    with tempfile.TemporaryDirectory() as d:
        archive(graph, d)
        (shell / "src" / "descriptor.rs").write_text(descriptor_rs(
            graph, id_=f"org.gestate.{name}", name=name,
            version=version, rate=rate))
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
