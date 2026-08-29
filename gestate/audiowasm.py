"""The graph as a `.wasm` — `card:online.md`, piece A.

`audiollvm.emit` writes one LLVM text and `audiollvm.build` turns it
into the shared object the desk plays.  This module turns the **same
text** into a wasm module for a browser to play: `clang --target=wasm32`
on the `.ll`, then `wasm-ld`.  Nothing is emitted differently for the
two targets, which is the whole claim — measured 2026-08-29 on
`twinkle.ges`, 176400/176400 frames bit-identical, and held from then
on by `test/test_wasm.py` across `examples/audio/`.

Three things the page side has to know are answered here rather than
in JavaScript, so the suite can check them:

* `imports_of(wasm)` — what the module wants from outside.  The
  emitter declares `llvm.exp.f64` and friends; LLVM lowers `floor`,
  `sqrt`, `minnum`, `maxnum` to wasm instructions and leaves `exp`,
  `log`, `sin`, `cos`, `pow` as calls.  The page supplies those from
  `Math`, and `HOST` is the same table for `run` below.
* The ABI is `audiollvm`'s: `render_block(state, out, want, slots)`
  with every pointer an offset into the module's own memory, the state
  `8 * (1 + Σ slots)` bytes of zeros, the output interleaved doubles.
  `run` is the reference for how a page lays that out.
* `wasmtime` is imported lazily by `run` and only there.  It is a bench
  tool (`tools/toolbox.sh`): the page runs the module in the browser,
  and `run` exists so the suite can hold the two renders together
  without one.
"""

from __future__ import annotations

import math
import shutil
import struct
import subprocess
from pathlib import Path

from .audioir import Graph
from .audiollvm import (_BUILD, _flags, _slots, emit, out_channels,
                        pack_control)

#: complaint  world — a tool this machine lacks, named: clang, wasm-ld or
#: wasmtime.  Nothing here is about the piece; the graph was already
#: accepted by the time it reaches a compiler.

#: What the module imports, and what supplies it — here and in the page.
#: Arity is what the page's `importObject` must match.
HOST = {"exp": (1, math.exp), "log": (1, math.log), "sin": (1, math.sin),
        "cos": (1, math.cos), "pow": (2, math.pow), "fmax": (2, max),
        "fmin": (2, min), "floor": (1, math.floor), "sqrt": (1, math.sqrt)}

#: `clang --target=wasm32` asks for `wasm-ld-<its major>` by name and
#: Ubuntu's clang package does not carry it (`tools/toolbox.sh`).  A
#: rustup toolchain ships one under `gcc-ld/` that links the same, so a
#: machine with Rust on it is often already past this.
LINKERS = ("wasm-ld", "wasm-ld-18", "wasm-ld-19", "wasm-ld-17", "wasm-ld-20")


class WasmError(Exception):
    """A tool this machine lacks, named."""


def find_linker() -> str | None:
    for name in LINKERS:
        found = shutil.which(name)
        if found:
            return found
    for path in sorted(Path.home().glob(
            ".rustup/toolchains/*/lib/rustlib/*/bin/gcc-ld/wasm-ld")):
        return str(path)
    return None


def missing() -> str | None:
    """Why `build` cannot run here, or `None`."""
    if shutil.which("clang") is None:
        return "no clang to compile the IR with"
    if find_linker() is None:
        return "no wasm-ld to link with (`tools/toolbox.sh`)"
    return None


def build(graph: Graph, directory, opt: str = "-O2",
          wants=("render_block",)) -> Path:
    """Compile the graph to `<directory>/synthN.wasm` and return its path.

    `wants` defaults to the double renderer alone: the page hands the
    doubles to an `AudioWorklet` as they are, and each extra renderer is
    another third of a second of clang.  No object store, unlike
    `audiollvm.build`: this is run by a page generator and a test, not
    at every editor start, and a cache is a second thing to be wrong.
    """
    why = missing()
    if why is not None:
        raise WasmError(why)
    directory = Path(directory)
    stem = f"synth{next(_BUILD)}"
    ll, obj, wasm = (directory / f"{stem}.ll", directory / f"{stem}.o",
                     directory / f"{stem}.wasm")
    ll.write_text(emit(graph, wants))
    # `-Wno-override-module`: the text names the host's triple, and
    # replacing it is the point rather than a warning.
    subprocess.run(["clang", "--target=wasm32", *_flags(opt),
                    "-Wno-override-module", "-c", "-o", str(obj), str(ll)],
                   check=True, capture_output=True)
    # `--allow-undefined` is what leaves `exp` as an import instead of a
    # link error; `--export-all` exports the memory and `__heap_base`,
    # which is how the host finds room for the state without a malloc.
    subprocess.run([find_linker(), "--no-entry", "--export-all",
                    "--allow-undefined", "-o", str(wasm), str(obj)],
                   check=True, capture_output=True)
    return wasm


def _leb(data: bytes, at: int) -> tuple:
    value = shift = 0
    while True:
        byte = data[at]
        at += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            return value, at


def imports_of(wasm) -> list:
    """`(module, name)` pairs the binary imports, read from the file.

    Parsed here rather than asked of `wasmtime` so the answer does not
    need the bench tool: a page generator wants this list to write the
    `importObject`, and the suite wants it to say every name is in `HOST`.
    """
    data = Path(wasm).read_bytes()
    if data[:4] != b"\0asm":
        #: complaint  machine — the linker's own output, checked before it is parsed
        raise WasmError(f"{wasm} is not a wasm binary")
    at, found = 8, []
    while at < len(data):
        kind = data[at]
        size, at = _leb(data, at + 1)
        end = at + size
        if kind == 2:                      # the import section
            count, at = _leb(data, at)
            for _ in range(count):
                n, at = _leb(data, at)
                module, at = data[at:at + n].decode(), at + n
                n, at = _leb(data, at)
                name, at = data[at:at + n].decode(), at + n
                desc = data[at]
                at += 1
                if desc == 0:              # function: a type index
                    _, at = _leb(data, at)
                elif desc == 1:            # table: reftype, limits
                    at += 1
                    at = _limits(data, at)
                elif desc == 2:            # memory: limits
                    at = _limits(data, at)
                else:                      # global: valtype, mutability
                    at += 2
                found.append((module, name))
        at = end
    return found


def _limits(data: bytes, at: int) -> int:
    flag = data[at]
    _, at = _leb(data, at + 1)
    if flag & 1:
        _, at = _leb(data, at)
    return at


def run(wasm, graph: Graph, control, samples: int, block: int) -> list:
    """Render through the module under `wasmtime` — `run_native`'s twin.

    Same shape of answer: floats for a mono graph, frame tuples
    otherwise, so `run(...) == run_native(...)` is the test.  The layout
    is the page's too: state at `__heap_base`, the output buffer after
    it, the control slots after that, and memory grown to fit.
    """
    try:
        import wasmtime
    except ImportError as e:
        raise WasmError("no `wasmtime` in this interpreter "
                        "(`tools/toolbox.sh`)") from e
    import ctypes

    store = wasmtime.Store()
    module = wasmtime.Module.from_file(store.engine, str(wasm))
    linker = wasmtime.Linker(store.engine)
    f64 = wasmtime.ValType.f64()
    for name, (arity, fn) in HOST.items():
        linker.define(store, "env", name, wasmtime.Func(
            store, wasmtime.FuncType([f64] * arity, [f64]), fn))
    inst = linker.instantiate(store, module)
    ex = inst.exports(store)
    mem, render = ex["memory"], ex["render_block"]
    heap = ex["__heap_base"].value(store)

    width = 8 * (1 + sum(_slots(graph, n) for n in graph.nodes))
    channels = out_channels(graph)
    sources = graph.control_sources()
    state, buf = heap, heap + width
    slots_at = buf + 8 * block * channels
    need = slots_at + 8 * max(1, len(sources)) + 16
    while mem.data_len(store) < need:
        mem.grow(store, 1)
    mem.write(store, bytes(width), state)

    slots = (ctypes.c_int64 * max(1, len(sources)))()
    out: list = []
    done = 0
    while done < samples:
        want = min(block, samples - done)
        pack_control(graph, slots, sources, control, done)
        mem.write(store, bytes(slots), slots_at)
        render(store, state, buf, want, slots_at)
        raw = mem.read(store, buf, buf + 8 * want * channels)
        out += struct.unpack(f"<{want * channels}d", raw)
        done += want
    if channels > 1:
        out = [tuple(out[i:i + channels])
               for i in range(0, len(out), channels)]
    return out
