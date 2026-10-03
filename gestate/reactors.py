"""`reactor` blocks — `card:gui-is-difficult.md` §"The next slice: two
checkboxes, as reactors", 2026-10-02.

A reactor is a component that owns what it does and nothing it shows:
its persistent state is the model's, reached through lenses
(`facts.ges` §"Lenses"); its **modes** say which reactions are live; its
**picture** names the port each region feeds.  A parent lays its
children's pictures out without knowing they are interactive, and a
press still reaches the child.

    reactor Checkbox (label : Text) (at : Lens Flags Bool)
      mode Off when not (get at)
        on press -> at = put at True
        picture = feeds press (box label False)
      mode On when get at
        on press -> at = put at False
        picture = feeds press (box label True)

    reactor Panel
      mute = new Checkbox "mute" (member flagRel "mute")
      solo = new Checkbox "solo" (member flagRel "solo")
      picture = Column mute.picture solo.picture

    substrate = Panel.picture flags

**Desugared into the signals the tree already has**, as Henri guessed
(*"the implementation may indeed fall out from the signals"*).  Each
reactor becomes `name__picture params… model`, a picture of the model;
a region that `feeds` a port becomes a `Does` carrying that port's
reactions in the current mode; `get l` reads the lens off the model and
`put l` is the lens's acts.  Static instances only: an instance is a
helper applied to its arguments, which is why this works — and why the
wall it meets is mutation, components that come and go.

**The block is blanked in place and its desugaring appended**, the
`include` rule (`notes.expanded`): no line of the author's file moves.

**Checked before anything compiles**, the signature declared and held
to (his answer 1, *"declared and checked"*):

* a body may `put` only into an effect its reaction declares, and an
  effect must be one of the reactor's lens parameters;
* `get` reads only a parameter;
* a region `feeds` only a port some reaction hears in that mode;
* **two reactions on one port writing one lens are refused when they
  can be live together** — in the same mode, or one outside every mode
  — and allowed in different modes, which never are (Schulz-Rosengarten
  et al., *Modal Reactors*, §VI-C).

*Modes here are derived, not set.*  A mode is live when its `when`
holds of the model — the first that holds, in the order written — so a
checkbox's mode is a view of its lens and holds no copy, where LF's
modes are stored and switched by transitions.

**And stored, since 2026-10-03** — `card:gui-is-difficult.md` §"The next
slice: a drag, as a reactor with a stored mode".  A mode with fields and
no `when` is set by a **hold** (`gui.ges`' `Holds`):

    reactor Dot (label : Text) (at : Lens Dots Int)
      mode Resting
        on grab x y -> Carrying x x
        picture = Shift (get at) 0 (hold (disc label restInk))
      mode Carrying (x0 : Int) (x : Int)
        on drag x1 y1 -> Carrying x0 x1
        on release -> Resting
        on release -> at = put at (get at + x - x0)
        picture = Shift (get at + x - x0) 0 (hold (disc label heldInk))

The modes are one data type, `DotMode`; a transition is a phase of the
hold to a mode, folded by `dot__step`; `on release -> <lens> = …` is the
commit, carried by the picture's `Holds` and performed on the release.
**Each instance has its own hold channel and its own mode** — a `scanE`
of the step over that channel — made at the root for every path to a
stored instance, which a static `new` is what allows.  So `X.picture`
outside the blocks is a signal of the model, `Sig m -> Sig Sub`.
A transition sees only its mode's fields and the hand; a hold writes
nothing while it moves; one reactor's modes are all stored or all
derived.

**And banks, the same day** — §"The next slice: the notes editor's note
hand".  An instance for every element of a collection the model holds,
keyed:

    reactor Roll (all : Lens Tune Tune)
      notes = new Note n (moving n) for n in elems (get all) by noteKey n
      picture = Over lane notes.picture

Instances come and go with the model — the mutation a static `new`
cannot make.  **A bank shares one hold channel**: a `Holds` carries the
key it was built with (`Hold key event`), the bank's state is the one
key held and its instance's mode (`NoteHeld k m`, or `NoteFree`), and an
instance's mode is that one when its key is the held key, its first
otherwise — one hand on a desktop holds one thing.

**And named holds, the same day** — §"The next slice: resize, on the
note hand", Henri's *"go with 1"*.  A picture may have more than one
part to take hold of, and names the others; a `grab` says which part it
begins on:

    reactor Note (n : NoteRow) (to : Lens Tune NoteRow)
      mode Resting
        on grab x y -> Carrying x y x y
        on grab end x y -> Sizing x x
        picture = onRoll n (Over (hold (noteBar n restInk)) (hold end (endOf n)))

The picture says where the end is, so the geometry is said once.  Each
name is a hold channel of its own (two to a reactor, in this slice),
both folded by the one step through `sync` (`reactors__scan2`); a drag
and a release arrive where their hold began, so only a `grab` names a
part, and a mode the hold is in draws its part under the same name — the
host performs the acts of the hold on the grabbed channel, as it stands
at the release.
"""
from __future__ import annotations

import re

from .notes import NotesError

GENERATED = "# ── generated from the reactor blocks above (gestate/reactors.py) ──"


#: complaint  author, unplaced — fixme.md F245: a reactor block refused before it compiles, its line said in words
class ReactorError(NotesError):
    """A reactor block refused before it compiles, at the author's line."""


_HEAD = re.compile(r"^reactor\s+([A-Z]\w*)\s*(.*?)\s*$")
_PARAM = re.compile(r"\(\s*([a-z]\w*)\s*:[^()]*(?:\([^()]*\)[^()]*)*\)")
_MODE = re.compile(r"^mode\s+([A-Z]\w*)\s+when\s+(.+)$")
#: A **stored** mode: no `when`, and the fields it carries — `mode
#: Carrying (x0 : Int) (x : Int)`.  Its modes are a data type, set by
#: transitions over a hold, not derived from the model.
_SMODE = re.compile(r"^mode\s+([A-Z]\w*)((?:\s*\(\s*[a-z]\w*\s*:[^()]*\))*)\s*$")
_FIELD = re.compile(r"\(\s*([a-z]\w*)\s*:\s*([^()]*?)\s*\)")
#: A transition, set by a phase of the hold: `on grab x y -> Carrying x x`.
_SHIFT = re.compile(r"^on\s+(grab|drag|release)((?:\s+[a-z_]\w*)*)\s*->\s*([A-Z].*)$")
_HOLD = re.compile(r"\bhold\b")
#: `hold` and the word after it, which is a part's name when a `grab`
#: names it — `hold end (endOf n)` — and the picture's own word otherwise.
_HOLD_PART = re.compile(r"\bhold\b(?:\s+([a-z]\w*))?")
#: A phase of a hold, and the `Event` it arrives as.
_PHASE = {"grab": "Press", "drag": "Move", "release": "Release"}
_ON = re.compile(r"^on\s+([a-z]\w*)\s*(?:->\s*([\w\s,]*?))?\s*=\s*(.*)$")
_PICTURE = re.compile(r"^picture\s*=\s*(.*)$")
_NEW = re.compile(r"^([a-z]\w*)\s*=\s*new\s+([A-Z]\w*)\s*(.*)$")
#: A **bank**: an instance for every element of a collection the model
#: holds, keyed — `notes = new Note n (moving n) for n in elems (get
#: score) by noteKey n`.  Instances come and go with the model.
_BANK = re.compile(r"^([a-z]\w*)\s*=\s*new\s+([A-Z]\w*)\s*(.*?)\s+for\s+([a-z]\w*)"
                   r"\s+in\s+(.+?)\s+by\s+(.+)$")
_GET = re.compile(r"\bget\s+([a-z]\w*)")
_PUT = re.compile(r"\bput\s+([a-z]\w*)")
_FEEDS = re.compile(r"\bfeeds\s+([a-z]\w*)")
_INST = re.compile(r"\b([a-z]\w*)\.picture\b")


def _low(name: str) -> str:
    return name[0].lower() + name[1:]


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _blank(line: str) -> bool:
    s = line.strip()
    return not s or s.startswith("#")


class _Item:
    """One line of a block and the lines indented under it."""

    def __init__(self, number: int, text: str, children: list):
        self.number, self.text, self.children = number, text, children

    def body(self) -> list[tuple[int, str]]:
        """The member's own text: its line, and its continuation lines."""
        out = [(self.number, self.text)]
        for c in self.children:
            out += c.body()
        return out


def _tree(lines: list[tuple[int, str]]) -> list[_Item]:
    """Lines indented under a line are its children, recursively."""
    items: list[_Item] = []
    i = 0
    while i < len(lines):
        number, raw = lines[i]
        depth = _indent(raw)
        j = i + 1
        while j < len(lines) and _indent(lines[j][1]) > depth:
            j += 1
        items.append(_Item(number, raw.strip(), _tree(lines[i + 1:j])))
        i = j
    return items


class _Reaction:
    def __init__(self, line, port, effects, body):
        self.line, self.port, self.effects, self.body = line, port, effects, body


class _Mode:
    def __init__(self, line, name, when, fields=None):
        self.line, self.name, self.when = line, name, when
        self.fields: list[tuple[str, str]] = fields or []
        self.stored = when is None and fields is not None
        self.reactions: list[_Reaction] = []
        self.shifts: list[tuple[int, str, list[str], str]] = []
        self.picture: list[tuple[int, str]] | None = None


class _Reactor:
    def __init__(self, line, name, params):
        self.line, self.name, self.params = line, name, params
        self.modes: list[_Mode] = []
        self.always = _Mode(line, "", None)          # what no mode holds
        self.instances: dict[str, tuple[int, str, str]] = {}
        #: name -> (line, reactor, arguments, variable, collection, key)
        self.banks: dict[str, tuple[int, str, str, str, str, str]] = {}

    @property
    def stored(self) -> bool:
        """Whether its modes are stored — set by a hold — not derived."""
        return any(m.stored for m in self.modes)

    @property
    def ports(self) -> list[str]:
        """The parts of its picture a hold can begin on: the unnamed one
        first, then each a `grab` names — a hold channel each."""
        named = sorted({sh[2] for m in self.modes for sh in m.shifts if sh[2]})
        return [""] + named


def _blocks(source: str) -> tuple[list[_Reactor], list[int]]:
    """The reactor blocks of `source`, and the line numbers they take."""
    lines = source.split("\n")
    found, taken = [], []
    i = 0
    while i < len(lines):
        head = _HEAD.match(lines[i])
        if not head:
            i += 1
            continue
        start = i
        j = i + 1
        while j < len(lines) and (_blank(lines[j]) or _indent(lines[j]) > 0):
            j += 1
        # trailing blank lines belong to what follows
        while j > i + 1 and not lines[j - 1].strip():
            j -= 1
        name, rest = head.group(1), head.group(2)
        params = _PARAM.findall(rest)
        r = _Reactor(start + 1, name, params)
        members = [(n + 1, lines[n]) for n in range(start + 1, j)
                   if not _blank(lines[n])]
        for item in _tree(members):
            _member(r, r.always, item)
        found.append(r)
        taken += list(range(start, j))
        i = j
    return found, taken


def _member(r: _Reactor, into: _Mode, item: _Item) -> None:
    place = f"line {item.number}"
    m = _MODE.match(item.text)
    if m:
        if into is not r.always:
            raise ReactorError(f"{place}: a mode inside a mode — nest a "
                               "modal reactor instead (Modal Reactors §IV-A)")
        mode = _Mode(item.number, m.group(1), m.group(2))
        if any(x.name == mode.name for x in r.modes):
            raise ReactorError(f"{place}: `{r.name}` has two modes named "
                               f"`{mode.name}`")
        r.modes.append(mode)
        for c in item.children:
            _member(r, mode, c)
        return
    m = _SMODE.match(item.text)
    if m:
        if into is not r.always:
            raise ReactorError(f"{place}: a mode inside a mode — nest a "
                               "modal reactor instead (Modal Reactors §IV-A)")
        mode = _Mode(item.number, m.group(1), None, _FIELD.findall(m.group(2)))
        if any(x.name == mode.name for x in r.modes):
            raise ReactorError(f"{place}: `{r.name}` has two modes named "
                               f"`{mode.name}`")
        r.modes.append(mode)
        for c in item.children:
            _member(r, mode, c)
        return
    m = _SHIFT.match(item.text)
    if m:
        if into is r.always:
            raise ReactorError(f"{place}: a transition belongs to the mode it "
                               "leaves — write it under a `mode`")
        binders = m.group(2).split()
        port = ""
        if len(binders) in (1, 3):
            if m.group(1) != "grab":
                raise ReactorError(
                    f"{place}: `on {m.group(1)} {binders[0]}` — a hold's part is "
                    f"named where it begins, on `grab`; a {m.group(1)} arrives "
                    f"where its hold began")
            port, binders = binders[0], binders[1:]
        if len(binders) not in (0, 2):
            raise ReactorError(f"{place}: `on {m.group(1)}` binds the hand's "
                               f"two coordinates or none, not {len(binders)}")
        body = " ".join([m.group(3)] + [t for c in item.children
                                        for _n, t in c.body()])
        into.shifts.append((item.number, m.group(1), port, binders, body))
        return
    m = _ON.match(item.text)
    if m:
        effects = [e.strip() for e in (m.group(2) or "").split(",") if e.strip()]
        body = [(item.number, m.group(3))] + [
            x for c in item.children for x in c.body()]
        into.reactions.append(_Reaction(item.number, m.group(1), effects, body))
        return
    m = _PICTURE.match(item.text)
    if m:
        if into.picture is not None:
            raise ReactorError(f"{place}: a second `picture` in "
                               f"`{into.name or r.name}`")
        into.picture = [(item.number, m.group(1))] + [
            x for c in item.children for x in c.body()]
        return
    m = _BANK.match(item.text)
    if m:
        if into is not r.always:
            raise ReactorError(f"{place}: a bank inside a mode is not in this "
                               "slice — make it at the reactor's level")
        name = m.group(1)
        if name in r.instances or name in r.banks:
            raise ReactorError(f"{place}: two instances named `{name}`")
        r.banks[name] = (item.number, m.group(2), m.group(3), m.group(4),
                         m.group(5), m.group(6))
        return
    m = _NEW.match(item.text)
    if m:
        if into is not r.always:
            raise ReactorError(f"{place}: an instance inside a mode is "
                               "not in this slice — instantiate at the "
                               "reactor's level")
        name = m.group(1)
        if name in r.instances or name in r.banks:
            raise ReactorError(f"{place}: two instances named `{name}`")
        r.instances[name] = (item.number, m.group(2), m.group(3))
        return
    raise ReactorError(
        f"{place}: a reactor holds `mode … when …` or `mode … (field : T)…`, "
        f"`on <port> -> <lens> = …`, `on grab|drag|release … -> <Mode> …`, "
        f"`picture = …` and `<name> = new <Reactor> …`; this line is none of them")


# ── the checks ────────────────────────────────────────────────────────────


def _check(r: _Reactor, known: set[str]) -> None:
    lenses = set(r.params)
    _check_stored(r)
    for mode in [r.always] + r.modes:
        for x in mode.reactions:
            for e in x.effects:
                if e not in lenses:
                    raise ReactorError(
                        f"line {x.line}: `on {x.port}` declares `{e}` as an "
                        f"effect, and `{r.name}` has no lens of that name — "
                        f"its parameters are {', '.join(f'`{p}`' for p in r.params) or 'none'}")
            for n, text in x.body:
                for put in _PUT.findall(text):
                    if put not in x.effects:
                        raise ReactorError(
                            f"line {n}: `put {put}` in a reaction that declares "
                            f"{', '.join(f'`{e}`' for e in x.effects) or 'no effect'} — "
                            f"a reaction writes only what its signature says; "
                            f"add `{put}` after the `->`")
        texts = [t for x in mode.reactions for t in x.body]
        texts += mode.picture or []
        if mode.when:
            texts += [(mode.line, mode.when)]
        for n, text in texts:
            for got in _GET.findall(text):
                if got not in lenses:
                    raise ReactorError(
                        f"line {n}: `get {got}` — `{r.name}` has no lens of that name")
    # a region feeds a port someone hears, in that mode
    for mode in [r.always] + r.modes:
        heard = {x.port for x in mode.reactions + r.always.reactions}
        for n, text in mode.picture or []:
            for port in _FEEDS.findall(text):
                if port not in heard:
                    where = f"mode `{mode.name}`" if mode.name else f"`{r.name}`"
                    raise ReactorError(
                        f"line {n}: this region feeds `{port}`, and no reaction "
                        f"in {where} hears `{port}`")
    # **two writers of one lens on one port, live together**
    for mode in r.modes or [r.always]:
        live = r.always.reactions + (mode.reactions if mode is not r.always else [])
        seen: dict[tuple[str, str], int] = {}
        for x in live:
            for e in x.effects:
                key = (x.port, e)
                if key in seen:
                    where = f"in mode `{mode.name}`" if mode.name else ""
                    raise ReactorError(
                        f"line {x.line}: two reactions on `{x.port}` write `{e}` "
                        f"{where} (the other on line {seen[key]}) — which runs "
                        f"first would be a choice nobody wrote down; put them "
                        f"in separate modes, or make them one reaction")
                seen[key] = x.line
    for name, (n, cls, _args) in r.instances.items():
        if cls not in known:
            raise ReactorError(f"line {n}: `new {cls}` — no reactor of that name")
    for name, (n, cls, *_rest) in r.banks.items():
        if cls not in known:
            raise ReactorError(f"line {n}: `new {cls}` — no reactor of that name")
    pictures = [t for m in [r.always] + r.modes for t in (m.picture or [])]
    for n, text in pictures:
        for inst in _INST.findall(text):
            if inst not in r.instances and inst not in r.banks:
                raise ReactorError(f"line {n}: `{inst}.picture` — `{r.name}` "
                                   f"has no instance named `{inst}`")


def _check_stored(r: _Reactor) -> None:
    """The rules a stored mode adds: one kind of mode to a reactor, a
    transition that sees only its mode's fields and the hand, one
    transition per phase per mode, a commit only on the release, and a
    `hold` only where there is a mode for it to set."""
    if r.stored and any(not m.stored for m in r.modes):
        bad = next(m for m in r.modes if not m.stored)
        raise ReactorError(
            f"line {bad.line}: `{r.name}` mixes a stored mode with a derived "
            f"one (`mode {bad.name} when …`) — a mode is set by a hold or read "
            f"off the model, and one reactor does one")
    names = {m.name for m in r.modes}
    if len(r.ports) > 2:
        raise ReactorError(
            f"line {r.line}: `{r.name}` names {len(r.ports) - 1} parts to take "
            f"hold of ({', '.join(f'`{x}`' for x in r.ports[1:])}) — one named "
            f"part beside the unnamed one is what this slice folds")
    for mode in r.modes:
        seen: dict[tuple, int] = {}
        for n, phase, port, binders, body in mode.shifts:
            said = f"{phase} {port}".strip()
            if (phase, port) in seen:
                raise ReactorError(
                    f"line {n}: two transitions on `{said}` in mode "
                    f"`{mode.name}` (the other on line {seen[phase, port]}) — the "
                    f"mode is one value and two writers of it is a choice "
                    f"nobody wrote down")
            seen[phase, port] = n
            head = body.split()[0]
            if head not in names:
                raise ReactorError(
                    f"line {n}: `-> {head}` — `{r.name}` has no mode of that "
                    f"name; its modes are {', '.join(f'`{x}`' for x in sorted(names))}")
            if _GET.search(body) or _PUT.search(body):
                raise ReactorError(
                    f"line {n}: a transition reads only its mode's fields and "
                    f"the hand — not the model (`get`) and not a lens (`put`); "
                    f"a commit is `on release -> <lens> = …`")
            for p in r.params:
                if re.search(rf"\b{p}\b", body):
                    raise ReactorError(
                        f"line {n}: a transition reads only its mode's fields "
                        f"and the hand, and `{p}` is a parameter")
        for x in mode.reactions:
            if x.port in ("grab", "drag") and x.effects:
                raise ReactorError(
                    f"line {x.line}: `on {x.port}` writes `{x.effects[0]}` — a "
                    f"hold writes nothing while the hand moves; its commit is "
                    f"`on release`")
    pictures = [t for m in [r.always] + r.modes for t in (m.picture or [])]
    if not r.stored:
        for n, text in pictures:
            if _HOLD.search(text):
                raise ReactorError(
                    f"line {n}: `hold` in `{r.name}`, which has no stored "
                    f"mode for the hold to set — give it `mode … (field : T)`")


# ── the desugaring ────────────────────────────────────────────────────────


def _expr(text_lines: list[tuple[int, str]], rewrite) -> list[str]:
    """An expression's lines, rewritten, the continuation lines kept
    under the first at the indentation they had relative to each other."""
    first = rewrite(text_lines[0][1])
    rest = [t for _n, t in text_lines[1:]]
    if not rest:
        return [first]
    least = min(_indent(t) for t in rest)
    return [first] + ["    " + rewrite(t[least:]) for t in rest]


def _define(name: str, args: list[str], body: list[str]) -> list[str]:
    head = f"{name} {' '.join(args)} = ".replace("  ", " ")
    return [head + body[0]] + body[1:] + [""]


def _slots(r: _Reactor, reactors: dict[str, _Reactor]) -> list[tuple]:
    """Every place under `r` that **stores** a mode, `r` itself first when
    it does: `("one", path)` for an instance, `("bank", path)` for a bank
    of stored instances — paths of instance names, `()` for `r`.  Each is
    a hold channel and a state signal, made once per path at the root: a
    static `new` is what lets every instance have its own, and a bank
    shares one, its state the one key held."""
    out = [("one", ())] if r.stored else []
    for name, (_n, cls, _given) in r.instances.items():
        out += [(kind, (name,) + p) for kind, p in _slots(reactors[cls], reactors)]
    for name, (_n, cls, *_rest) in r.banks.items():
        if reactors[cls].stored:
            out.append(("bank", (name,)))
    return out


def _slot_cls(r: _Reactor, path: tuple, reactors: dict[str, _Reactor]) -> _Reactor:
    """The stored reactor a slot's path under `r` comes to."""
    cls = r
    for name in path:
        cls = reactors[(cls.instances.get(name) or cls.banks[name])[1]]
    return cls


def _holds(i: int, parts: int) -> list[str]:
    """A slot's hold channels, one a part: `__h0`, then `__h0_1`."""
    return [f"__h{i}"] + [f"__h{i}_{p}" for p in range(1, parts)]


def _arg_names(kind: str, i: int, parts: int = 1) -> list[str]:
    return _holds(i, parts) + ([f"__k{i}", f"__s{i}"] if kind == "one" else [f"__b{i}"])


def _slot_args(r: _Reactor, reactors: dict[str, _Reactor]) -> list[str]:
    return [a for i, (kind, path) in enumerate(_slots(r, reactors))
            for a in _arg_names(kind, i, len(_slot_cls(r, path, reactors).ports))]


def _ctor(r: _Reactor, mode: _Mode) -> str:
    return f"{r.name}{mode.name}"


def _first(r: _Reactor) -> str:
    """The first mode, as a value — its fields zero."""
    m = r.modes[0]
    return " ".join([_ctor(r, m)] + ["0" for _f in m.fields])


def _modes_type(r: _Reactor) -> list[str]:
    """The stored modes as one data type, a constructor a mode."""
    alts = " | ".join(" ".join([_ctor(r, m)] + [t for _f, t in m.fields])
                      for m in r.modes)
    return [f"{r.name}Mode := {alts}", ""]


_EVENTS = (("Tick", 0), ("Move", 2), ("Press", 2), ("Release", 2), ("Key", 1))


def _others(taken: set, pad: str, result: str) -> list[str]:
    """The `Event` alternatives not already written, each to `result`."""
    return [f"{pad}{' '.join([e] + [f'__a{k}' for k in range(n)])} -> {result}"
            for e, n in _EVENTS if e not in taken]


def _step(r: _Reactor) -> list[str]:
    """`<r>__step : Int -> <R>Mode -> Hold -> <R>Mode` — the transitions,
    a phase of the hold to a mode; any other event leaves the mode be.
    The `Int` is the part the hold arrived on, `ports`' index: a `grab`
    reads it, and nothing else does."""
    base = _low(r.name)
    names = [m.name for m in r.modes]

    def ctors(text: str) -> str:
        return re.sub(r"\b(" + "|".join(names) + r")\b",
                      lambda m: f"{r.name}{m.group(1)}", text)

    lines = [f"{base}__step __p __s __h = case __h of",
             "    Hold __k __e -> case __s of"]
    ports = r.ports
    for mode in r.modes:
        fields = " ".join(f for f, _t in mode.fields)
        lines.append(f"        {_ctor(r, mode)} {fields}".rstrip() + " -> case __e of")
        taken = set()
        for phase in ("grab", "drag", "release"):
            mine = [sh for sh in mode.shifts if sh[1] == phase]
            if not mine:
                continue
            event = _PHASE[phase]
            taken.add(event)
            if phase != "grab" or all(not sh[2] for sh in mine) and len(ports) == 1:
                _n, _ph, _port, binders, body = mine[0]
                x, y = binders or ["__x", "__y"]
                lines.append(f"            {event} {x} {y} -> {ctors(body)}")
                continue
            # a grab, told apart by the part it began on
            lines.append(f"            {event} __gx __gy -> " + _by_port(mine, ports, ctors))
        lines += _others(taken, "            ", "__s")
    return lines + [""]


def _by_port(grabs: list, ports: list[str], ctors) -> str:
    """The grab transitions of one mode as one expression of `__p`: each
    part's own, and the mode left be on a part with none."""
    def one(port: str) -> str:
        sh = next((g for g in grabs if g[2] == port), None)
        if sh is None:
            return "__s"
        _n, _ph, _port, binders, body = sh
        x, y = binders or ["__x", "__y"]
        return f"(({x} {y} => {ctors(body)}) __gx __gy)"
    out = one(ports[-1])
    for i in range(len(ports) - 2, -1, -1):
        out = f"(reactors__pick (__p == {i}) {one(ports[i])} {out})"
    return out


def _bank_kit(c: _Reactor) -> list[str]:
    """What a bank of `c` needs, once per reactor banked: its state — the
    one key held and that instance's mode, or none — the step over the
    bank's channel, and an instance's mode read back off it."""
    base, C = _low(c.name), c.name
    first = c.modes[0]
    fields = " ".join("__f" + str(k) for k in range(len(first.fields)))
    return ([f"{C}Bank := {C}Free | {C}Held Float {C}Mode", ""]
            + [f"{base}__bankStep __p __b __h = case __h of",
               "    Hold __k __e -> case __b of",
               f"        {C}Free -> case __e of",
               f"            Press __x __y -> {base}__settle __k ({base}__step __p ({_first(c)}) __h)"]
            + _others({"Press"}, "            ", "__b")
            + [f"        {C}Held __j __m -> {base}__settle __j ({base}__step __p __m (Hold __j __e))", ""]
            + [f"{base}__settle __k __m = case __m of",
               f"    {_ctor(c, first)} {fields}".rstrip() + f" -> {C}Free"]
            + [f"    {_ctor(c, m)} " + " ".join(f"__f{k}" for k in range(len(m.fields)))
               + f" -> {C}Held __k __m" for m in c.modes[1:]]
            + ["", f"{base}__modeOf __k __b = case __b of",
               f"    {C}Free -> {_first(c)}",
               f"    {C}Held __j __m -> case __j == __k of",
               "        True -> __m",
               f"        False -> {_first(c)}", ""])


def _parts() -> list[str]:
    """What a reactor with a named part needs, once: a choice of two
    modes, and the fold of two hold channels into one state — `scanE`
    over `sync`, whichever arrived (`signal.ges`' `zipSig` is the same
    move over signals)."""
    return ["reactors__pick __c __a __b = case __c of",
            "    True -> __a",
            "    False -> __b", "",
            "reactors__scan2 : (b -> a -> b) -> (b -> a -> b) -> b -> ExL a -> ExL a -> Sig b",
            "reactors__scan2 = gfix q => (f g z e1 e2 => z ::: (delay (q2 s => case s of",
            "    SyncLeft x -> q2 f g (f z x) e1 e2",
            "    SyncRight y -> q2 f g (g z y) e1 e2",
            "    SyncBoth x y -> q2 f g (g (f z x) y) e1 e2) <*> q <@> sync e1 e2))", ""]


def _over() -> list[str]:
    return ["reactors__over __xs = case __xs of",
            "    [] -> Gap 0 0",
            "    __x :: __r -> Over __x (reactors__over __r)", ""]


def _desugar_one(r: _Reactor, reactors: dict[str, _Reactor]) -> list[str]:
    base = _low(r.name)
    slots = _slot_args(r, reactors)
    args = r.params + slots + ["__m"]
    out: list[str] = [f"# reactor {r.name}, line {r.line}"]
    if r.stored:
        out += _modes_type(r) + _step(r)

    def margs(mode: _Mode) -> list[str]:
        """A mode's own functions see its fields, bound by the dispatch."""
        return r.params + slots + [f for f, _t in mode.fields] + ["__m"]

    def rewrite_for(mode: _Mode):
        a = " ".join(margs(mode))

        def rw(text: str) -> str:
            text = _GET.sub(lambda m: f"(lensGet {m.group(1)} __m)", text)
            text = _PUT.sub(lambda m: f"lensPut {m.group(1)}", text)
            text = _FEEDS.sub(lambda m: f"({base}__{mode.name or '_'}__feeds_{m.group(1)} "
                                        f"{a})", text)
            text = _INST.sub(lambda m: f"({base}__{m.group(1)}__picture {' '.join(args)})",
                             text)
            if mode.stored:
                def held(m):
                    part = m.group(1)
                    if part in r.ports[1:]:
                        return (f"Holds __h0_{r.ports.index(part)} __k0 "
                                f"({base}__{mode.name}__release {a})")
                    tail = f" {part}" if part else ""
                    return f"Holds __h0 __k0 ({base}__{mode.name}__release {a}){tail}"
                text = _HOLD_PART.sub(held, text)
            return text
        return rw

    mine = _slots(r, reactors)
    for name, (n, cls, given) in r.instances.items():
        child = reactors[cls]
        passed = []
        for kind, p in _slots(child, reactors):
            at = mine.index((kind, (name,) + p))
            passed += _arg_names(kind, at, len(_slot_cls(child, p, reactors).ports))
        call = " ".join([f"{_low(cls)}__picture", rewrite_for(r.always)(given)]
                        + passed + ["__m"])
        out += _define(f"{base}__{name}__picture", args, [call])
    for name, (n, cls, given, var, coll, key) in r.banks.items():
        child = reactors[cls]
        rw = rewrite_for(r.always)
        if child.stored:
            at = mine.index(("bank", (name,)))
            k = f"({rw(key)})"
            passed = _holds(at, len(child.ports)) + [k, f"({_low(cls)}__modeOf {k} __b{at})"]
        else:
            passed = []
        each = " ".join([f"{_low(cls)}__picture", rw(given)] + passed + ["__m"])
        out += _define(f"{base}__{name}__picture", args,
                       [f"reactors__over (map ({var} => {each}) ({rw(coll)}))"])
    for mode in [r.always] + r.modes:
        rw = rewrite_for(mode)
        tag = mode.name or "_"
        ma = margs(mode) if mode is not r.always else args
        live = r.always.reactions + (mode.reactions if mode is not r.always else [])
        for port in sorted({x.port for x in live if x.port != "release" or not r.stored}):
            acts = [x for x in live if x.port == port]
            for k, x in enumerate(acts):
                out += _define(f"{base}__{tag}__on_{port}_{k}", ma, _expr(x.body, rw))
            joined = " ++ ".join(f"{base}__{tag}__on_{port}_{k} {' '.join(ma)}"
                                 for k in range(len(acts)))
            out += _define(f"{base}__{tag}__feeds_{port}", ma + ["__s"],
                           [f"Does ({joined}) __s"])
        if mode.stored:
            commits = [x for x in mode.reactions if x.port == "release"]
            for k, x in enumerate(commits):
                out += _define(f"{base}__{tag}__on_release_{k}", ma, _expr(x.body, rw))
            joined = " ++ ".join(f"{base}__{tag}__on_release_{k} {' '.join(ma)}"
                                 for k in range(len(commits))) or "Nil"
            out += _define(f"{base}__{tag}__release", ma, [joined])
        if mode.picture is not None:
            out += _define(f"{base}__{tag}__picture", ma, _expr(mode.picture, rw))
        if mode.when:
            out += _define(f"{base}__{tag}__when", args, [rw(mode.when)])
    # the picture: the mode the reactor is in, else the reactor's own
    fallback = (f"{base}_____picture {' '.join(args)}" if r.always.picture is not None
                else "Gap 0 0")
    if r.stored:
        body = ["case __s0 of"]
        for mode in r.modes:
            fields = " ".join(f for f, _t in mode.fields)
            pic = (f"{base}__{mode.name}__picture {' '.join(margs(mode))}"
                   if mode.picture is not None else fallback)
            body.append(f"    {_ctor(r, mode)} {fields}".rstrip() + f" -> {pic}")
        out += _define(f"{base}__picture", args, body)
        return out
    # Laid out as a block, one alternative a line — the one-line form was
    # F244 when this was written, and the block reads as well.
    body = [fallback]
    for mode in reversed(r.modes):
        pic = (f"{base}__{mode.name}__picture {' '.join(args)}"
               if mode.picture is not None else fallback)
        body = ([f"case {base}__{mode.name}__when {' '.join(args)} of",
                 f"    True -> {pic}",
                 f"    False -> {body[0]}"]
                + ["    " + line for line in body[1:]])
    out += _define(f"{base}__picture", args, body)
    return out


def _root(r: _Reactor, reactors: dict[str, _Reactor]) -> list[str]:
    """`X.picture` outside the blocks: **a signal of the model**, `Sig m ->
    Sig Sub`.  Each slot under `X` gets its hold channel and its state — a
    `scanE` over that channel of the stored reactor's step, or of its
    bank's — and the view is the picture applied to them and the model."""
    base = _low(r.name)
    slots = _slots(r, reactors)
    out = [f"# the root {r.name}: a hold channel and a state for each of its "
           f"{len(slots)} stored place(s)"]
    passed, states = [], []
    for i, (kind, path) in enumerate(slots):
        owner, cls = r, r
        for name in path:
            owner = cls
            cls = reactors[(cls.instances.get(name) or cls.banks[name])[1]]
        tag = "__".join(path) or "self"
        hold, state = f"{base}__{tag}__hold", f"{base}__{tag}__state"
        holds = [hold] + [f"{hold}_{p}" for p in cls.ports[1:]]
        c = _low(cls.name)
        start = (f"({_first(cls)})" if kind == "one" else f"{cls.name}Free")
        step = f"{c}__step" if kind == "one" else f"{c}__bankStep"
        for h in holds:
            out += [f"{h} : Chan Hold", f"{h} = chan", ""]
        if len(holds) == 1:
            out += [f"{state} = scanE ({step} 0) {start} (wait {hold})", ""]
        else:
            out += [f"{state} = reactors__scan2 ({step} 0) ({step} 1) {start} "
                    f"(wait {holds[0]}) (wait {holds[1]})", ""]
        passed += holds + (["0.0", f"__s{i}"] if kind == "one" else [f"__s{i}"])
        states.append(state)
    params = " ".join(r.params)
    picture = " ".join(x for x in (f"{base}__picture", params, " ".join(passed), "__m") if x)
    # **Two signals to a `!`, never more.**  The states are gathered into
    # one signal first — a tuple of them, no set in it — and the view is
    # lifted over that and the model: `!` over three or more signals
    # refuses a function that runs a comprehension over a set (F246),
    # and a lens's `get` is exactly that.
    if len(states) > 1:
        names = [f"__s{k}" for k in range(len(states))]
        tup = "(" + ", ".join(names) + ")"
        out += _define(f"{base}__gather", names, [tup])
        out += [f"{base}__states = !{base}__gather {' '.join(states)}", ""]
        out += _define(f"{base}__view", r.params + ["__ss", "__m"],
                       ["case __ss of", f"    {tup} -> {picture}"])
        joined = f"{base}__states"
    else:
        out += _define(f"{base}__view",
                       r.params + [f"__s{k}" for k in range(len(states))] + ["__m"],
                       [picture])
        joined = states[0] if states else ""
    view = " ".join(x for x in (f"{base}__view", params) if x)
    sig = (f"map ({view}) __sm" if not states
           else f"!{view} {joined} __sm" if not r.params
           else f"!({view}) {joined} __sm")
    out += _define(f"{base}__picture_sig", r.params + ["__sm"], [sig])
    return out


def desugar(source: str) -> str:
    """`source` with its reactor blocks blanked in place and their
    desugaring appended; unchanged, and free, when it has none."""
    if not re.search(r"^reactor\s", source, re.M):
        return source
    reactors, taken = _blocks(source)
    known = {r.name for r in reactors}
    for r in reactors:
        _check(r, known)
    by_name = {r.name: r for r in reactors}
    lines = source.split("\n")
    for n in taken:
        lines[n] = ""
    text = "\n".join(lines)
    # `Panel.picture` outside the blocks is the reactor's picture as a
    # signal of the model — a stored mode under it is a signal too
    roots = []

    def root(m):
        if m.group(1) not in known:
            return m.group(0)
        if m.group(1) not in roots:
            roots.append(m.group(1))
        return f"{_low(m.group(1))}__picture_sig"

    text = re.sub(r"\b([A-Z]\w*)\.picture\b", root, text)
    generated = [GENERATED, ""]
    banked = []
    for r in reactors:
        for _n, cls, *_rest in r.banks.values():
            if cls not in banked:
                banked.append(cls)
    if banked:
        generated += _over()
    if any(len(r.ports) > 1 for r in reactors):
        generated += _parts()
    for r in reactors:
        generated += _desugar_one(r, by_name)
        if r.name in banked and r.stored:
            generated += _bank_kit(r)
    for name in roots:
        generated += _root(by_name[name], by_name)
    return text.rstrip("\n") + "\n\n" + "\n".join(generated)
