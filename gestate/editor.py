"""The editor, driven from here — `shell/editor` over a C ABI.

**Rust owns the rope and the window; this orchestrates.**  A keystroke
never crosses the boundary: it arrives in the window's own loop, the
rope takes it, the frame is redrawn, all in microseconds.  What crosses
is a *version* — one atomic read — so this side can ask "did anything
happen" as often as it likes and only fetch the text when it has.

That division is the same one `spec/substrate.md` §"Why one window"
argued for the pygame view, in the register that turned out to matter:
`audioeditor.Workbench` imports no toolkit, so a view is a second view
against the same object.  This is that view, in Rust, and `Workbench`
stays the model — it decides what the file is, when a rebuild is worth
doing and when to save.  The editor never learns any of that and by
construction cannot.

    from gestate.editor import Editor

    ed = Editor(open("thing.ges").read())
    while ed.is_open:
        if ed.changed():
            workbench.rebuild(ed.text)
        time.sleep(0.03)

The library is built at need and loaded once, exactly as
`gestate/crust.py` does for `libcrust.so`.
"""

from __future__ import annotations

import ctypes
from pathlib import Path


class EditorError(Exception):
    pass


_LIB = None


def _stale(so, crate) -> bool:
    """Has the crate moved since the library was built?

    **The whole window used to be built once and then never again.**  The
    check was `if not so.exists()`, so an edit to the Rust took effect
    the next time somebody deleted the `.so` and not before — and the
    editor that came up was silently the one from whenever that was.
    That is the worst shape a defect can have here: everything works,
    nothing is reported, and the thing you just changed is not in the
    room.  It cost an afternoon of looking for a key binding that was
    already right.

    Cheap enough to do every start: a few dozen `stat`s against one, and
    `cargo` is asked to rebuild only when one of them is newer.  Cargo
    would work this out too, but only if it is run, and the point is that
    it was not.
    """
    try:
        built = so.stat().st_mtime
    except OSError:
        return True
    watched = [crate / "Cargo.toml"]
    watched.extend((crate / "src").rglob("*.rs"))
    # `gestate-panel` is compiled into it — a painter change is a window
    # change, and the two crates are one artifact by the time it matters.
    panel = crate.parent / "panel"
    if panel.is_dir():
        watched.append(panel / "Cargo.toml")
        watched.extend((panel / "src").rglob("*.rs"))
    return any(p.stat().st_mtime > built for p in watched if p.exists())


def _library():
    """The cdylib, built at need and loaded once per process."""
    global _LIB
    if _LIB is not None:
        return _LIB
    import shutil
    import subprocess

    root = Path(__file__).resolve().parent.parent
    crate = root / "shell" / "editor"
    so = crate / "target" / "release" / "libgestate_editor.so"
    if not so.exists() or _stale(so, crate):
        if shutil.which("cargo") is None:
            raise EditorError(
                "no libgestate_editor.so and no cargo to build it — "
                "`cargo build --release --features capi` in `shell/editor/` "
                "makes one")
        done = subprocess.run(
            ["cargo", "build", "--release", "--quiet", "--features", "capi",
             "--target-dir", str(crate / "target")],
            cwd=crate, capture_output=True, text=True)
        if done.returncode != 0:
            raise EditorError("the editor did not build:\n" + done.stderr)
    lib = ctypes.CDLL(str(so))

    # Hand-declared, like `crust.py`'s and like `shell/clap/src/abi.rs`:
    # the subset that is used, owned line for line, with no binding
    # generator in the build.
    lib.ged_open.argtypes = [ctypes.c_char_p, ctypes.c_int32, ctypes.c_int32]
    lib.ged_open.restype = ctypes.c_void_p
    lib.ged_is_open.argtypes = [ctypes.c_void_p]
    lib.ged_is_open.restype = ctypes.c_bool
    lib.ged_version.argtypes = [ctypes.c_void_p]
    lib.ged_version.restype = ctypes.c_uint64
    lib.ged_pos.argtypes = [ctypes.c_void_p]
    lib.ged_pos.restype = ctypes.c_size_t
    # `c_void_p`, not `c_char_p`: ctypes converts a `c_char_p` result to
    # bytes and drops the pointer, and the pointer is what
    # `ged_free_str` needs back.  The same trap `crust.py` records.
    lib.ged_text.argtypes = [ctypes.c_void_p]
    lib.ged_text.restype = ctypes.c_void_p
    lib.ged_set_text.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.ged_set_text.restype = None
    lib.ged_load_text.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.ged_load_text.restype = None
    lib.ged_load_new.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.ged_load_new.restype = None
    lib.ged_free_str.argtypes = [ctypes.c_void_p]
    lib.ged_free_str.restype = None
    lib.ged_set_furniture.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.ged_set_furniture.restype = None
    lib.ged_gestures.argtypes = [ctypes.c_void_p]
    lib.ged_gestures.restype = ctypes.c_void_p
    lib.ged_order.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.ged_order.restype = None
    lib.ged_set_picture.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.ged_set_picture.restype = None
    lib.ged_request_close.argtypes = [ctypes.c_void_p]
    lib.ged_request_close.restype = None
    lib.ged_close.argtypes = [ctypes.c_void_p]
    lib.ged_close.restype = None
    _LIB = lib
    return lib


class Editor:
    """An editor window, open until it is closed.

    Positions are **characters**, which is what the rope indexes and
    what a caret means — never bytes.  Python agrees about that for
    free, and it is the reason the boundary carries no encoding
    argument.
    """

    def __init__(self, text: str = "", width: int = 1000, height: int = 700):
        self._lib = _library()
        self._h = self._lib.ged_open(text.encode(), width, height)
        if not self._h:
            raise EditorError("the editor window would not open")
        self._seen = 0

    @property
    def is_open(self) -> bool:
        return bool(self._h) and bool(self._lib.ged_is_open(self._h))

    @property
    def version(self) -> int:
        """How many edits have happened — one atomic read."""
        return 0 if not self._h else int(self._lib.ged_version(self._h))

    @property
    def pos(self) -> int:
        """Where the caret is, as a character offset."""
        return 0 if not self._h else int(self._lib.ged_pos(self._h))

    @property
    def text(self) -> str:
        """What the document says now."""
        if not self._h:
            return ""
        p = self._lib.ged_text(self._h)
        if not p:
            return ""
        try:
            return ctypes.cast(p, ctypes.c_char_p).value.decode()
        finally:
            self._lib.ged_free_str(p)

    @text.setter
    def text(self, value: str) -> None:
        """Replace the text, undoably.  The window picks it up on its
        next frame — and keeps its histories, so a `fmt` through here
        stays one undo away from the text you had."""
        if self._h:
            self._lib.ged_set_text(self._h, value.encode())

    def load(self, value: str) -> None:
        """Replace the text *and its past* — what a file switch does.

        **A different file is a different past** (`fixme.md` F113): the
        setter above commits, so a switch through it left the old
        file's whole content one undo away under the new file's name —
        and one save from overwriting the new file with the old one.
        """
        if self._h:
            self._lib.ged_load_text(self._h, value.encode())

    def load_new(self, value: str) -> None:
        """`load`, for a file that does not exist yet.

        The text loads *unsaved* — "saving creates it" means it is not
        written down, and a phantom that read as saved gave a person no
        tell that the file under them was a starter wearing a borrowed
        name (the lantern that was not the lantern).
        """
        if self._h:
            self._lib.ged_load_new(self._h, value.encode())

    def changed(self) -> bool:
        """Whether the text has moved since this last said so.

        **The whole polling protocol.**  Call it as often as you like —
        it is an atomic read and a comparison — and only reach for
        `.text` when it answers yes, because *that* is a copy of the
        whole document.
        """
        now = self.version
        if now == self._seen:
            return False
        self._seen = now
        return True

    def describe(self, furniture: str) -> None:
        """Tell the window what the chrome says.

        **Whole, not a diff**, and only when something changed — a diff
        would be a second state to keep in step across a boundary, and
        the description is a few hundred bytes.
        """
        if self._h:
            self._lib.ged_set_furniture(self._h, furniture.encode())

    def gestures(self) -> list:
        """Everything the window has said since this was last called.

        **Drained, not read**, so nothing is seen twice: a command run
        because the queue was polled again is the sort of bug that plays
        a note nobody asked for.
        """
        if not self._h:
            return []
        p = self._lib.ged_gestures(self._h)
        if not p:
            return []
        try:
            text = ctypes.cast(p, ctypes.c_char_p).value.decode()
        finally:
            self._lib.ged_free_str(p)
        return [line for line in text.split("\n") if line]

    def draw(self, picture: str) -> None:
        """The canvas, as shapes — see `shell/editor/src/shapes.rs`.

        **Its own channel, not part of the description.**  A substrate
        animates, so this changes every frame while the furniture beside
        it changes when a command runs; sending them together would
        carry every knob and command line across the boundary sixty
        times a second to move one dot.
        """
        if self._h:
            self._lib.ged_set_picture(self._h, picture.encode())

    def order(self, line: str) -> None:
        """Ask the window to do something — see `furniture::Order`.

        **Queued, not called.**  Undo, the zoom and the caret are the
        window's own state and live on the window's thread; an order is
        how a command reaches them without anything off that thread
        touching the rope.  It happens on the next frame, which is the
        same fifteen milliseconds a keystroke takes.
        """
        if self._h:
            self._lib.ged_order(self._h, line.encode())

    def request_close(self) -> None:
        """Ask the window to shut.  Returns at once."""
        if self._h:
            self._lib.ged_request_close(self._h)

    def close(self) -> None:
        """Shut it and wait for the loop to come back."""
        if self._h:
            self._lib.ged_close(self._h)
            self._h = None

    def __enter__(self) -> "Editor":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:                                # noqa: BLE001
            pass
