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
    if not so.exists():
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
    lib.ged_free_str.argtypes = [ctypes.c_void_p]
    lib.ged_free_str.restype = None
    lib.ged_set_furniture.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.ged_set_furniture.restype = None
    lib.ged_gestures.argtypes = [ctypes.c_void_p]
    lib.ged_gestures.restype = ctypes.c_void_p
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
        """Load text.  The window picks it up on its next frame."""
        if self._h:
            self._lib.ged_set_text(self._h, value.encode())

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
