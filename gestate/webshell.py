"""The picture's shell as a `.wasm` — `card:audiovisual-gallery.md`, day two.

    python -m gestate.webshell -o site/     # build it, say where it went

`shell/web` is the seam a page draws a substrate through: `crust` and
`gestate_panel`'s `Sub` walk compiled for `wasm32` and offered as C
functions over one flat `i32` buffer.  This module is what *builds* it
from Python, so `gestate.online` can put it beside a page the way
`audiowasm.build` puts the synth there.

**One module for the whole gallery, not one per piece.**  The synth is
the piece — every `.ges` compiles to its own — but the canvas driver is
the *same program* for all of them, and what differs is the substrate
it is handed at `web_open`.  So the site carries it once at the root and
each page fetches `../gestate_web.wasm`; a single-piece site gets its
own copy beside the page, because there is no root to share.

**It imports nothing**, which is `crust`'s zero-dependency rule reaching
the browser: the page supplies the machine no host functions and no
glue.  `test_gallery.py` holds that, and holds the picture equal to what
`gestate/gui.py` draws.

**Cargo is the only thing that can be missing**, and it is named rather
than guessed at: a machine without the `wasm32-unknown-unknown` target
is one `rustup target add` away, and a page generator that cannot build
this leaves the piece's sound alone and drops only its picture.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: The browser's target, and where cargo leaves the artefact.  Kept out
#: of the workspace `target/` for the reason `test_gallery.py` gives: a
#: wasm build must not throw away the artifacts a native `cargo test`
#: just made.
TRIPLE = "wasm32-unknown-unknown"
TARGET = ROOT / "shell" / "web" / "target"
NAME = "gestate_web.wasm"

#: complaint  world — a toolchain this machine lacks, named.  Nothing
#: here is about the piece: the substrate was already serialized by the
#: time a compiler is asked for anything.


class ShellError(Exception):
    """The builder refusing, with the reason."""


def missing() -> str | None:
    """Why `build` cannot run here, or `None`."""
    if shutil.which("cargo") is None:
        return "no cargo to build the picture's shell with"
    if shutil.which("rustup") is None:
        return "no rustup, so the wasm32 target cannot be checked for"
    out = subprocess.run(["rustup", "target", "list", "--installed"],
                         capture_output=True, text=True)
    if TRIPLE not in out.stdout:
        return f"no {TRIPLE} target (`rustup target add {TRIPLE}`)"
    return None


def build(directory=None) -> Path:
    """Build `shell/web` for `wasm32` and return the module's path.

    With `directory`, the module is copied there under `NAME` and that
    copy is returned; without one, cargo's own artefact path is.  The
    build is cached by cargo itself, which is why there is no second
    cache here — one afternoon's measurement had it at 1.6 s cold.
    """
    why = missing()
    if why is not None:
        raise ShellError(why)
    subprocess.run(["cargo", "build", "--quiet", "--release",
                    "-p", "gestate-web", "--target", TRIPLE,
                    "--target-dir", str(TARGET)],
                   cwd=ROOT, check=True)
    made = TARGET / TRIPLE / "release" / NAME
    if not made.exists():                                 # pragma: no cover
        raise ShellError(f"cargo built nothing at {made}")
    if directory is None:
        return made
    out = Path(directory) / NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(made, out)
    return out


def main(argv=None) -> int:
    import argparse
    import sys

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-o", "--out", default=None,
                    help="directory to copy the module into")
    args = ap.parse_args(argv)
    try:
        path = build(args.out)
    except ShellError as e:
        print(f"gestate.webshell: {e}", file=sys.stderr)
        return 2
    print(f"{path} — {path.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
