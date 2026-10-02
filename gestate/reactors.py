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

    substrate = map Panel.picture flags

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
modes are stored and switched by transitions.  A transient mode — a drag
under way — is the next slice's, not this one's.
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
_ON = re.compile(r"^on\s+([a-z]\w*)\s*(?:->\s*([\w\s,]*?))?\s*=\s*(.*)$")
_PICTURE = re.compile(r"^picture\s*=\s*(.*)$")
_NEW = re.compile(r"^([a-z]\w*)\s*=\s*new\s+([A-Z]\w*)\s*(.*)$")
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
    def __init__(self, line, name, when):
        self.line, self.name, self.when = line, name, when
        self.reactions: list[_Reaction] = []
        self.picture: list[tuple[int, str]] | None = None


class _Reactor:
    def __init__(self, line, name, params):
        self.line, self.name, self.params = line, name, params
        self.modes: list[_Mode] = []
        self.always = _Mode(line, "", None)          # what no mode holds
        self.instances: dict[str, tuple[int, str, str]] = {}


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
    m = _NEW.match(item.text)
    if m:
        if into is not r.always:
            raise ReactorError(f"{place}: an instance inside a mode is "
                               "not in this slice — instantiate at the "
                               "reactor's level")
        name = m.group(1)
        if name in r.instances:
            raise ReactorError(f"{place}: two instances named `{name}`")
        r.instances[name] = (item.number, m.group(2), m.group(3))
        return
    raise ReactorError(
        f"{place}: a reactor holds `mode … when …`, `on <port> -> <lens> = …`, "
        f"`picture = …` and `<name> = new <Reactor> …`; this line is none of them")


# ── the checks ────────────────────────────────────────────────────────────


def _check(r: _Reactor, known: set[str]) -> None:
    lenses = set(r.params)
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
    pictures = [t for m in [r.always] + r.modes for t in (m.picture or [])]
    for n, text in pictures:
        for inst in _INST.findall(text):
            if inst not in r.instances:
                raise ReactorError(f"line {n}: `{inst}.picture` — `{r.name}` "
                                   f"has no instance named `{inst}`")


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


def _desugar_one(r: _Reactor, reactors: dict[str, _Reactor]) -> list[str]:
    base = _low(r.name)
    args = r.params + ["__m"]
    out: list[str] = [f"# reactor {r.name}, line {r.line}"]

    def rewrite_for(mode: _Mode):
        def rw(text: str) -> str:
            text = _GET.sub(lambda m: f"(lensGet {m.group(1)} __m)", text)
            text = _PUT.sub(lambda m: f"lensPut {m.group(1)}", text)
            text = _FEEDS.sub(lambda m: f"({base}__{mode.name or '_'}__feeds_{m.group(1)} "
                                        f"{' '.join(args)})", text)
            text = _INST.sub(lambda m: f"({base}__{m.group(1)}__picture {' '.join(args)})",
                             text)
            return text
        return rw

    for name, (n, cls, given) in r.instances.items():
        child = reactors[cls]
        out += _define(f"{base}__{name}__picture", args,
                       [f"{_low(cls)}__picture {rewrite_for(r.always)(given)} __m"])
    for mode in [r.always] + r.modes:
        rw = rewrite_for(mode)
        tag = mode.name or "_"
        live = r.always.reactions + (mode.reactions if mode is not r.always else [])
        for port in sorted({x.port for x in live}):
            acts = [x for x in live if x.port == port]
            for k, x in enumerate(acts):
                out += _define(f"{base}__{tag}__on_{port}_{k}", args, _expr(x.body, rw))
            joined = " ++ ".join(f"{base}__{tag}__on_{port}_{k} {' '.join(args)}"
                                 for k in range(len(acts)))
            out += _define(f"{base}__{tag}__feeds_{port}", args + ["__s"],
                           [f"Does ({joined}) __s"])
        if mode.picture is not None:
            out += _define(f"{base}__{tag}__picture", args, _expr(mode.picture, rw))
        if mode.when:
            out += _define(f"{base}__{tag}__when", args, [rw(mode.when)])
    # the picture: the first mode whose `when` holds, else the reactor's own
    fallback = (f"{base}_____picture {' '.join(args)}" if r.always.picture is not None
                else "Gap 0 0")
    # Laid out as a block, one alternative a line: a one-line
    # `case … of True -> a; False -> b` carried on into the next
    # definition when it was tried (2026-10-02).
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
    # `Panel.picture` outside the blocks is the reactor's picture function
    text = re.sub(r"\b([A-Z]\w*)\.picture\b",
                  lambda m: f"{_low(m.group(1))}__picture" if m.group(1) in known
                  else m.group(0), text)
    generated = [GENERATED, ""]
    for r in reactors:
        generated += _desugar_one(r, by_name)
    return text.rstrip("\n") + "\n\n" + "\n".join(generated)
