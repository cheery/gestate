"""`GESTATE_BUILD_TIME=1` — where a rebuild's seconds go.

**The compile-side twin of `GESTATE_EDITOR_TIME`.**  The frame side has
a stopwatch and two lag tools, and consequently does not rot; the build
side had neither, and that is exactly how a rebuild measured at 400 ms
when stage 7.5 shipped became **twelve seconds** on `quartet.ges` with
two thousand tests passing.  Nothing was broken.  Nothing was watching.

    GESTATE_BUILD_TIME=1 python -m gestate.workbench examples/audio/quartet.ges

Every rebuild then writes one block to stderr:

    [build] quartet.ges 8.02s
              front end   4.56s
               assemble   0.80s
                extract   0.32s
                  clang   3.01s
                  knobs   0.28s
                  holes   0.07s
             ‖ substrate   0.51s
                 ‖ score   1.10s

**`‖` marks a phase that ran while another thread was in one too**,
which is not decoration: `Workbench.start` walks the canvas, the score
and the `FromMIDI` instances on a side thread while `clang` holds no
GIL, so those seconds overlap the ones beside them and the column does
not add up to the total.  A report that hid that would be read as
arithmetic and be wrong.

It is a claim about the *clock*, not about thread identity, and the
difference matters here: `pipeline._deep_stack` runs the front end on a
worker and waits for it, which is another thread and is not
concurrency.  So the mark comes from overlapping spans.

Each phase reports its **own** time: a phase inside another — the hole
scan inside the knob placement — is counted once, as itself, and its
caller's number excludes it.  What is left over from the total is the
work no phase is named for, which is the honest way to notice that
something unmeasured got expensive.

The phases are named where the work is, not here — `pipeline`,
`audiollvm`, `audioperform` and `audioeditor` each say `with phase(…)`
around what they own, so a phase cannot drift away from the code it
measures.  Off, `phase` hands back a shared do-nothing object and costs
an attribute lookup and a branch.
"""

from __future__ import annotations

import os
import sys
import threading
import time

__all__ = ["building", "phase"]


class _Off:
    """What `phase` returns when nobody is timing.  A `with` on this is
    two method calls that do nothing, which is the price of leaving the
    instrumentation in the code rather than in a patch somebody has to
    re-apply."""

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


_OFF = _Off()

#: The rebuild being timed, or `None`.  One at a time deliberately: a
#: second `building` inside or beside the first is *ignored* rather than
#: nested, because the outermost one is the wall clock a person is
#: actually waiting on, and two overlapping reports would say less than
#: one.  `Workbench.start` overtaken by another file is that case.
_current: "_Build | None" = None
_lock = threading.Lock()


class _Build:
    __slots__ = ("label", "began", "phases", "spans")

    def __init__(self, label: str):
        self.label = label
        self.began = time.perf_counter()
        #: name → [own seconds, how many times]
        self.phases: dict[str, list] = {}
        #: (name, start, end, thread) per phase run — kept because `‖`
        #: is a claim about *time*, and thread identity alone cannot
        #: make it: `pipeline._deep_stack` hands the front end to a
        #: worker and waits for it, which is another thread and is not
        #: concurrency.  Two phases are parallel when they overlap on
        #: the clock and are not each other's caller.
        self.spans: list = []

    def add(self, name, took, began, ended, thread) -> None:
        with _lock:
            row = self.phases.setdefault(name, [0.0, 0])
            row[0] += took
            row[1] += 1
            self.spans.append((name, began, ended, thread))

    def _parallel(self) -> set:
        """The phases that ran while something on another thread did."""
        out = set()
        for name, t0, t1, thread in self.spans:
            for other, u0, u1, mine in self.spans:
                if mine != thread and u0 < t1 and t0 < u1:
                    out.add(name)
                    out.add(other)
        return out

    def report(self) -> str:
        total = time.perf_counter() - self.began
        beside = self._parallel()
        lines = [f"[build] {self.label} {total:.2f}s"]
        for name, (took, count) in sorted(self.phases.items(),
                                          key=lambda kv: -kv[1][0]):
            if took < 0.005:
                continue
            shown = f"‖ {name}" if name in beside else name
            times = f"  ×{count}" if count > 1 else ""
            lines.append(f"  {shown:>22s}   {took:5.2f}s{times}")
        return "\n".join(lines)


#: The phases open on *this* thread, innermost last.  A phase inside
#: another — `_find_holes` inside `_place` — would otherwise be counted
#: twice, once as itself and once inside its caller, and a column that
#: double-counts is worse than no column.  So what each phase reports is
#: its *own* time and the caller's excludes it.
_open = threading.local()


class _Phase:
    __slots__ = ("name", "began", "build", "children")

    def __init__(self, name: str, build: _Build):
        self.name, self.build = name, build
        self.children = 0.0

    def __enter__(self):
        stack = getattr(_open, "stack", None)
        if stack is None:
            stack = _open.stack = []
        stack.append(self)
        self.began = time.perf_counter()
        return self

    def __exit__(self, *_exc):
        ended = time.perf_counter()
        took = ended - self.began
        stack = _open.stack
        stack.pop()
        if stack:
            stack[-1].children += took
        self.build.add(self.name, took - self.children, self.began, ended,
                       threading.get_ident())
        return False


def phase(name: str):
    """Time this stretch as `name`, when a rebuild is being timed."""
    build = _current
    return _Phase(name, build) if build is not None else _OFF


class _Building:
    __slots__ = ("label", "build")

    def __init__(self, label: str):
        self.label = label
        self.build = None

    def __enter__(self):
        global _current
        # Asked here rather than at import, so that setting the variable
        # in a test — or in a shell before the editor starts — is read
        # the same way, and nothing has to care what imported first.
        if os.environ.get("GESTATE_BUILD_TIME", "") in ("", "0"):
            return self
        with _lock:
            if _current is not None:
                return self            # the outer one owns the clock
            self.build = _current = _Build(self.label)
        return self

    def __exit__(self, *_exc):
        global _current
        if self.build is None:
            return False
        # Printed even when the build *failed*: a rebuild that spent
        # four seconds and then refused the edit is exactly the one you
        # want the numbers for.
        print(self.build.report(), file=sys.stderr, flush=True)
        with _lock:
            _current = None
        return False


def building(label: str):
    """Time one rebuild end to end and report it, if asked to."""
    return _Building(label)
