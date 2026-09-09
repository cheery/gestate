"""Executable statecharts, loaded and driven — `gestate/chart.ges`.

**A chart is a `.ges` value the editor runs**, the way `command.ges` is
a `.ges` file the editor reads: `chart.ges` in front of the subsystem's
own file, compiled once by the reference G-machine, and then
`advance chart state event` applied per event — about twenty
microseconds a step after a 0.2 s compile (measured 2026-09-07).  The
host executes the actions a step answers with; the chart never touches
the world itself, which is the per-subsystem law `chart.ges` states.

Terms cross the seam as plain Python: a constructor is a tuple with its
name first, `("Up", ("Playing",))`; an `Int` is an `int`; a `List` is a
`list`.  `card:gui-is-difficult.md` §"The first slice".
"""

from __future__ import annotations

from pathlib import Path

from . import gmachine as gm
from .gmachine import run
from .pipeline import compile as compile_program

HERE = Path(__file__).parent
LIBRARY = HERE / "chart.ges"


#: complaint  author, nowhere — a chart file missing a declaration, or a term built for a constructor the file does not have: the fault is a name absent from a file, and an absent name has no line
class ChartError(Exception):
    """A chart that could not be loaded, or a term it does not know."""


class Terms:
    """A library and one file, compiled, with values readable from Python.

    **Not chart-specific**, which is why it is its own class: a
    statechart was the first `.ges` value the host read back and it is
    not the last — `gestate/facts.py` reads a document's kinds through
    exactly this.  What is chart-specific is `Chart` below.
    """

    def __init__(self, path: Path, library: Path):
        self.path, self.library = Path(path), Path(library)
        source = (self.library.read_text(encoding="utf-8") + "\n"
                  + self.path.read_text(encoding="utf-8")
                  + "\nmain : Int\nmain = 0\n")
        self.state = compile_program(source)
        self._tag = {k: v.tag for k, v in self.state.cons.items()}
        self._name = {v.tag: k for k, v in self.state.cons.items()}

    def declared(self, name: str):
        """The global `name`, or a refusal that says which file lacks it."""
        try:
            return self.state.globals[name]
        except KeyError:
            raise ChartError(f"{self.path.name} declares no `{name}`") from None

    @property
    def constructors(self) -> set:
        """Every constructor name the file and the library declare."""
        return set(self._tag)

    # -- terms ----------------------------------------------------------------

    def node(self, term):
        """A Python term as a heap node."""
        if isinstance(term, bool):
            return gm.NCon(self._tag["True" if term else "False"], ())
        if isinstance(term, int):
            return gm.NNum(term)
        if isinstance(term, list):
            out = gm.NCon(self._tag["Nil"], ())
            for item in reversed(term):
                out = gm.NCon(self._tag["Cons"], (self.node(item), out))
            return out
        if isinstance(term, tuple) and term and isinstance(term[0], str):
            head, *args = term
            if head not in self._tag:
                raise ChartError(f"{self.path.name} has no constructor `{head}`")
            return gm.NCon(self._tag[head], tuple(self.node(a) for a in args))
        if isinstance(term, tuple):
            # A bare tuple — the product `beside` makes of two states.
            return gm.NCon(gm.tuple_tag(len(term)),
                           tuple(self.node(a) for a in term))
        raise ChartError(f"not a term: {term!r}")

    def read(self, node):
        """A heap node as a Python term, forced as far as it goes."""
        from .midi import _force

        node = _force(node, self.state)
        while isinstance(node, gm.NInd) and node.target is not None:
            node = node.target
        if isinstance(node, gm.NNum):
            return node.n
        if not isinstance(node, gm.NCon):
            raise ChartError(f"a chart answered a {type(node).__name__}, not a value")
        head = self._name.get(node.tag)
        if head == "Nil":
            return []
        if head == "Cons":
            out, at = [], node
            while isinstance(at, gm.NCon) and self._name.get(at.tag) == "Cons":
                out.append(self.read(at.args[0]))
                at = _force(at.args[1], self.state)
                while isinstance(at, gm.NInd) and at.target is not None:
                    at = at.target
            return out
        args = tuple(self.read(a) for a in node.args)
        # A tuple carries no name and comes back as a bare tuple.
        return (head, *args) if head is not None else args

    def _apply(self, fn, *args):
        node = fn
        for a in args:
            node = gm.NAp(node, a)
        self.state.stack, self.state.dump = [node], []
        self.state.code = [gm.Eval()]
        run(self.state)
        return self.state.stack[0]


class Chart(Terms):
    """One subsystem's chart, compiled, with its terms readable from Python."""

    def __init__(self, path: Path, name: str):
        super().__init__(path, LIBRARY)
        self.name = name
        self._chart = self.declared(name)
        self._advance = self.declared("advance")
        self._initial = self.declared("initial")

    # -- running it -----------------------------------------------------------

    def initial(self):
        return self.read(self._apply(self._initial, self._chart))

    def advance(self, state, event) -> tuple:
        """`(new state or None, actions)` — `None` is `Stay`."""
        got = self.read(self._apply(self._advance, self._chart,
                                    self.node(state), self.node(event)))
        if got == ("Stay",):
            return None, []
        _go, new, actions = got
        return new, actions


_LOADED: dict = {}


def load(name: str) -> Chart:
    """The chart `name`, from `gestate/<name>.ges`, compiled once per
    edit of either file."""
    path = HERE / f"{name}.ges"
    stamp = (path.stat().st_mtime_ns, LIBRARY.stat().st_mtime_ns)
    found = _LOADED.get(name)
    if found is None or found[0] != stamp:
        found = _LOADED[name] = (stamp, Chart(path, name))
    return found[1]
