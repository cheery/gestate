"""atlas.py — the project drawn from what it is, not from what it was.

`doc/atlas/whole.svg` is one A3 sheet of this repository: what you
write, what reads it, what runs it, the three backends, and the live
environment around them.  It is **generated**, and that is the whole
point of it.

**A drawing is believed longer than prose is.**  A hand-drawn
architecture map is wrong within a fortnight of the first refactor and
keeps being trusted for months after that, because nothing about a
picture says how old it is.  So almost nothing here is drawn: the
modules come from the filesystem, the arrows are checked against real
imports, the libraries and the crates are read off disk, and
`test_atlas.py` fails when the committed sheet is not what today's
source renders — the same guarantee `doc/ref/` has, and the same
sentence when it breaks: *run `python -m gestate.atlas`*.

What a person writes is exactly two things, and both are the parts a
machine cannot know:

* **`WHERE` — which lane each module belongs to.**  A dependency graph
  of fifty-nine modules and two hundred and sixty-six edges is a hairball
  that answers no question anybody has; a lane is a claim about *what a
  module is for*, and there is no deriving that.  Every module must be
  in it, which is why a new one fails the test rather than quietly
  going missing from the picture.
* **`SPINE` — which arrows tell the story.**  Not every import: the
  ones that are the path from text to sound.  Each names a real import
  that must exist, so an arrow cannot outlive the call behind it.

Kept in this file rather than in a data file beside it, because each
entry wants the sentence that justifies it and this project keeps such
tables where their comments can live (`session.WEIGHTS` is the same
shape).

**Deterministic on purpose**: no timestamp, no commit hash, sorted
everywhere.  A generated file that changes when nothing changed is a
generated file people stop regenerating.

The run also leaves a `.png` beside the sheet, because an `.svg` is a
file many readers cannot open.  That one is **not** committed and not
checked: raster bytes differ between rasterisers and between versions
of one, so the guarantee above cannot cover it, and a generated file
with no guarantee is the drift this file exists to prevent wearing a
different suffix.  `.gitignore` says the same thing where somebody
would look for it.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

#: The sheet, in millimetres.  A3 landscape, because it is meant to be
#: printed and stuck on a wall beside the fridge note.
PAGE_W, PAGE_H = 420.0, 297.0
MARGIN = 12.0


# ---------------------------------------------------------------------------
# The two hand-written tables
# ---------------------------------------------------------------------------

#: Module → lane.  **Every module must appear**, and `test_atlas.py`
#: says so by name when one does not: a module nobody placed is a module
#: missing from the picture, which is exactly the drift this file exists
#: to prevent.
WHERE: dict[str, str] = {
    # ── What the text becomes ───────────────────────────────────────────
    "syntax.tokenize": "surface", "syntax.parse": "surface",
    "syntax.ast": "surface", "syntax.rename": "surface",
    "syntax.descend": "surface",
    "prelude": "surface", "declarations": "surface", "desugar": "surface",
    "match": "surface", "envexpand": "surface", "helpers": "surface",
    "internals": "surface",
    # ── What it means ───────────────────────────────────────────────────
    "types": "types", "unify": "types", "infer": "types",
    "typecheck": "types", "kindcheck": "types", "constraint": "types",
    "coherence": "types", "elaborate": "types", "specialise": "types",
    "deriving": "types", "exhaust": "types", "subgrammar": "types",
    "monotone": "types", "changes": "types", "bottoms": "types",
    "seminaive": "types",
    # ── What runs it ────────────────────────────────────────────────────
    "expr": "core", "lift": "core", "gmachine": "core", "show": "core",
    "reactive": "core", "pipeline": "core", "crust": "core",
    # ── The three backends ──────────────────────────────────────────────
    "midi": "music", "tempo": "music",
    "gui": "gui",
    "audio": "sound", "audioextract": "sound", "audiograph": "sound",
    "audioir": "sound", "audiollvm": "sound", "audiovoices": "sound",
    "audioscore": "sound", "audioschedule": "sound", "audioalloc": "sound",
    "audiodynamic": "sound", "audiomidi": "sound", "transcript": "sound",
    # ── Playing it, and shipping it ─────────────────────────────────────
    "audioengine": "play", "audiolive": "play", "audiohost": "play",
    "audioperform": "play", "export": "play",
    # ── The window ──────────────────────────────────────────────────────
    "session": "window", "sessionlog": "window", "audioeditor": "window",
    "workbench": "window", "audiospans": "window", "scorebox": "window",
    "editor": "window", "buildtime": "window",
    # ── The tree, describing itself ─────────────────────────────────────
    "reference": "written", "atlas": "written",
}

#: The arrows worth drawing, each with what proves it.
#: `(from lane, to lane, what crosses, proof)`, where the proof is a
#: `(importer, imported)` pair that must be a real import — or a path
#: that must exist, for the one crossing that is not a Python call at
#: all.  So an arrow cannot outlive the thing behind it.
SPINE: list[tuple[str, str, str, object]] = [
    ("surface", "types", "declarations", ("typecheck", "declarations")),
    ("types", "core", "supercombinators", ("pipeline", "elaborate")),
    ("core", "music", "a forced score", ("midi", "gmachine")),
    ("core", "gui", "a forced scene", ("gui", "gmachine")),
    ("core", "sound", "the graph", ("audioextract", "gmachine")),
    ("sound", "play", "machine code", ("audiolive", "audiollvm")),
    ("window", "play", "an edit, under the sound",
     ("audioeditor", "audiolive")),
    ("window", "native", "furniture, down a pipe",
     "shell/editor/src/furniture.rs"),
]

#: What each lane is, in one sentence.  The editorial half — a lane
#: title says what a thing is called and this says what it is for.
LANES: dict[str, tuple[str, str]] = {
    "written": ("What you write",
                "A `.ges` file and the libraries in scope for it — each "
                "backend looks for one declaration.  The two below read "
                "this tree and write it back out: `doc/ref/`, and this "
                "sheet."),
    "surface": ("The surface",
                "Text to declarations: tokens, layout, patterns, "
                "the prelude that every file is assembled with."),
    "types": ("What it means",
              "Inference, classes and their instances, the Datafun "
              "and audio subgrammars — every refusal is written here."),
    "core": ("What runs it",
             "Supercombinators on a graph machine, in Python for the "
             "reference and in Rust (`crust`) for the window."),
    "music": ("Music", "`score` and `bpm`, performed to timed events."),
    "gui": ("Pictures", "`substrate : Sig Sub`, forced at frame rate."),
    "sound": ("Sound, compiled",
              "`sound : Sig Float` leaves the interpreter: the "
              "first-order fragment is extracted to a graph, the graph "
              "to C, the C to a `.so` by `clang`."),
    "play": ("Playing it",
             "The engine fills a buffer, the C host owns the card, and "
             "an edit is installed under the sound without stopping it."),
    "window": ("The window",
               "`command.ges` is the command list; the model holds the "
               "text and what is playing, and sends the shell furniture."),
    "native": ("Not Python",
               "The window, the painter, the plugin and the audio "
               "callback.  The G-machine is here twice on purpose: the "
               "Python one is the reference the other answers to."),
}

#: The libraries, and the one declaration each backend looks for.  Read
#: off disk for their existence; what they *supply* is this project's own
#: sentence about them and is written here.
SUPPLIES: list[tuple[str, str]] = [
    ("prelude.ges", "the language itself"),
    ("signal.ges", "the shared signal vocabulary"),
    ("music.ges", "`score`, `bpm` — a piece"),
    ("gui.ges", "`substrate : Sig Sub` — a picture"),
    ("audio.ges", "`sound : Sig Float` — an instrument"),
    ("synth.ges", "voices, envelopes, filters"),
    ("command.ges", "the editor's own vocabulary"),
]

#: The other half of the program, which is not Python.  Paths are
#: checked; the sentences are ours.
NATIVE: list[tuple[str, str, str]] = [
    ("crust", "crust/Cargo.toml", "the G-machine in Rust"),
    ("gestate-editor", "shell/editor/Cargo.toml", "the window"),
    ("gestate-panel", "shell/panel/Cargo.toml", "the painter"),
    ("gestate-clap", "shell/clap/Cargo.toml", "the plugin"),
    ("host.c", "gestate/host.c", "the audio callback"),
]

#: What comes out the far end, per backend.
WRITES: dict[str, str] = {
    "music": "a `.mid`",
    "gui": "a window, and a plugin tab",
    "sound": "a `.wav`, a `.so`, a `.clap`",
}


# ---------------------------------------------------------------------------
# The facts
# ---------------------------------------------------------------------------

def modules(root: Path) -> list[str]:
    """Every module in the package, `syntax.` ones spelled with their dot."""
    found = [p.stem for p in (root / "gestate").glob("*.py")
             if p.stem != "__init__"]
    found += [f"syntax.{p.stem}" for p in (root / "gestate" / "syntax").glob("*.py")
              if p.stem != "__init__"]
    return sorted(found)


def imports(root: Path) -> dict[str, set]:
    """Module → the modules of this package it imports.

    Read from the syntax tree rather than by importing anything: this
    runs in a test, and importing `audiohost` to find out what it needs
    would open a sound card to draw a picture.
    """
    known = set(modules(root))
    out: dict[str, set] = {}
    for name in known:
        path = (root / "gestate" / (name.replace(".", "/") + ".py"))
        try:
            tree = ast.parse(path.read_text())
        except (OSError, SyntaxError):                    # noqa: PERF203
            out[name] = set()
            continue
        deps: set = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.level:
                deps.add(node.module)
                deps.update(f"{node.module}.{a.name}" for a in node.names)
            elif isinstance(node, ast.Import):
                deps.update(a.name.removeprefix("gestate.")
                            for a in node.names if a.name.startswith("gestate."))
        out[name] = {d for d in deps if d in known}
    return out


def unplaced(root: Path) -> list[str]:
    """Modules with no lane — what a person has to answer for."""
    return sorted(set(modules(root)) - set(WHERE))


def phantom(root: Path) -> list[str]:
    """Lanes' modules that no longer exist."""
    return sorted(set(WHERE) - set(modules(root)))


def unproven(root: Path) -> list[str]:
    """Drawn arrows with nothing behind them any more."""
    edges = imports(root)
    out = []
    for a, b, _what, via in SPINE:
        if isinstance(via, str):
            if not (root / via).exists():
                out.append(f"{a} → {b} (claims {via})")
        elif via[1] not in edges.get(via[0], ()):
            out.append(f"{a} → {b} (claims {via[0]} imports {via[1]})")
    return out


def missing_files(root: Path) -> list[str]:
    """Named libraries and crates that are not there."""
    gone = [name for name, _s in SUPPLIES
            if not (root / "gestate" / name).exists()]
    gone += [f"{name} ({where})" for name, where, _s in NATIVE
             if not (root / where).exists()]
    return gone


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

@dataclass
class Box:
    """One lane on the sheet: a title, a sentence, and what is in it.

    `chips` are module names, laid out as rows of tags; `pairs` are a
    name with a sentence beside it, one to a line; `extra` is loose
    prose under both.  `h` is a *floor* — the drawing grows past it when
    the lane has more in it than that.
    """
    key: str
    x: float
    y: float
    w: float
    h: float
    tint: str
    chips: list = field(default_factory=list)
    extra: list = field(default_factory=list)
    pairs: list = field(default_factory=list)
    #: How far down the content reached — set when the lane is measured,
    #: and what keeps a sideways arrow off the text it passes.
    used: float = 0.0


def _esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _ticked(text: str) -> str:
    """`code` in a sentence, as a tspan that is drawn in the mono face."""
    out, mono = [], False
    for part in _esc(text).split("`"):
        if part:
            out.append(f'<tspan class="mono">{part}</tspan>' if mono else part)
        mono = not mono
    return "".join(out)


def _chip_w(name: str, size: float = 2.7) -> float:
    """How wide a chip has to be for its name.  Measured against DejaVu
    Sans Mono, whose advance is 0.602 em — the one number this file
    assumes about a font, and it only decides wrapping."""
    return len(name) * size * 0.602 + 3.4


def _chips(names: list, x: float, y: float, w: float,
           size: float = 2.7) -> tuple[list, float]:
    """Lay names out as rows of chips inside `w`, and say how tall it got."""
    out, cx, cy = [], x, y
    for name in names:
        cw = _chip_w(name, size)
        if cx > x and cx + cw > x + w:
            cx, cy = x, cy + 5.6
        out.append(f'<rect class="chip" x="{cx:.2f}" y="{cy:.2f}" '
                   f'width="{cw:.2f}" height="4.6" rx="1.2"/>'
                   f'<text class="chiptext" x="{cx + cw / 2:.2f}" '
                   f'y="{cy + 3.2:.2f}">{_esc(name)}</text>')
        cx += cw + 1.6
    return out, cy + 4.6 - y


def _wrap(text: str, width: float, size: float) -> list:
    """Break a sentence to fit `width` millimetres at `size`."""
    per = size * 0.52                       # a proportional face's average
    room = max(8, int(width / per))
    lines, line = [], ""
    for word in text.split():
        bare = re.sub(r"`", "", word)
        if line and len(re.sub(r"`", "", line)) + 1 + len(bare) > room:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines


def _lane(box: Box) -> tuple[list, float]:
    """One lane, drawn: frame, title, sentence, chips, footnotes.

    Returns what to draw and **how tall it had to be**, which is how a
    lane is sized: by what is in it.  A fixed height would be a guess
    that goes wrong the first time a lane gains a module, and the
    picture would be mostly air until it did.
    """
    title, note = LANES[box.key]
    out = [f'<text class="lanetitle" x="{box.x + 4:.2f}" '
           f'y="{box.y + 7.4:.2f}">{_esc(title)}</text>']
    y = box.y + 12.2
    for line in _wrap(note, box.w - 8, 2.9):
        out.append(f'<text class="note" x="{box.x + 4:.2f}" '
                   f'y="{y:.2f}">{_ticked(line)}</text>')
        y += 3.7
    for name, what in box.pairs:
        cw = _chip_w(name)
        out.append(f'<rect class="chip" x="{box.x + 4:.2f}" '
                   f'y="{y - 2.2:.2f}" width="{cw:.2f}" height="4.6" '
                   f'rx="1.2"/>'
                   f'<text class="chiptext" x="{box.x + 4 + cw / 2:.2f}" '
                   f'y="{y + 1:.2f}">{_esc(name)}</text>'
                   f'<text class="extra" x="{box.x + 6 + cw:.2f}" '
                   f'y="{y + 1:.2f}">{_esc(what)}</text>')
        y += 6.4
    if box.chips:
        y += 1.4
        chips, tall = _chips(sorted(box.chips), box.x + 4, y, box.w - 8)
        out += chips
        y += tall + 2.6
    for line in box.extra:
        out.append(f'<text class="extra" x="{box.x + 4:.2f}" '
                   f'y="{y:.2f}">{_ticked(line)}</text>')
        y += 3.8
    tall = max(box.h, y - box.y + 1.6)
    frame = (f'<rect class="lane" x="{box.x:.2f}" y="{box.y:.2f}" '
             f'width="{box.w:.2f}" height="{tall:.2f}" rx="2.4" '
             f'style="fill:{box.tint}"/>')
    return [frame, *out], tall


def _arrow(points: list, label: str = "", turn: bool = False,
           above: float | None = None) -> list:
    """An arrow through the given points, with its label at the first leg.

    **Elbows rather than diagonals.**  A straight line between two lanes
    on different rows crosses whatever is between them, which on a sheet
    this dense is a title; a leg down, a leg across and a leg down again
    goes round the outside and reads as a route.
    """
    path = " ".join(("M" if i == 0 else "L") + f"{x:.2f},{y:.2f}"
                    for i, (x, y) in enumerate(points))
    out = [f'<path class="edge" d="{path}" marker-end="url(#tip)"/>']
    if label:
        (x1, y1), (x2, y2) = points[0], points[1]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if above is not None:
            my = above                      # clear of what it points at
        spin = (f' transform="rotate(-90 {mx:.2f} {my:.2f})"' if turn else "")
        out.append(f'<text class="edgetext" x="{mx:.2f}" y="{my - 1.4:.2f}"'
                   f'{spin}>{_esc(label)}</text>')
    return out


def render(root: Path) -> str:
    """The whole sheet."""
    place = {}
    for name, lane in WHERE.items():
        place.setdefault(lane, []).append(name)

    inner = PAGE_W - 2 * MARGIN
    w4 = (inner - 3 * 6) / 4
    w3 = (inner - 2 * 6) / 3

    def across(n: int, i: int, w: float) -> float:
        return MARGIN + i * (w + 6)

    # **The three rows are the three sentences of the picture**: a file
    # becomes a program, a program is read by one of three backends, and
    # the audio one has a life of its own around it.  Row three sits
    # under row two's own column — `play` beneath `sound` — so the arrow
    # between them is a drop rather than a diagonal across the page.
    rows = [
        [Box("written", across(4, 0, w4), 0, w4, 0, "#f6f2ea",
             place.get("written", []),
             pairs=[(name, what) for name, what in SUPPLIES]),
         Box("surface", across(4, 1, w4), 0, w4, 0, "#eef3f7",
             place.get("surface", [])),
         Box("types", across(4, 2, w4), 0, w4, 0, "#eef3f7",
             place.get("types", [])),
         Box("core", across(4, 3, w4), 0, w4, 0, "#eaf1ee",
             place.get("core", []))],
        [Box(key, across(3, i, w3), 0, w3, 0, "#f3eef5", place.get(key, []),
             extra=[f"writes {WRITES[key]}"])
         for i, key in enumerate(("music", "gui", "sound"))],
        [Box("native", across(3, 0, w3), 0, w3, 0, "#eeeeee",
             pairs=[(name, what) for name, _where, what in NATIVE]),
         Box("window", across(3, 1, w3), 0, w3, 0, "#f7f0ea",
             place.get("window", [])),
         Box("play", across(3, 2, w3), 0, w3, 0, "#f7f0ea",
             place.get("play", []))],
    ]

    # Measured, then placed: a row is as tall as its tallest lane, and
    # what is left over on the page becomes the gaps between rows rather
    # than a margin at the bottom.
    tall = []
    for row in rows:
        for box in row:
            box.used = _lane(box)[1]
        tall.append(max(b.used for b in row))
    top = MARGIN + 21.0
    gap = 13.0
    over = PAGE_H - MARGIN - 7 - top - sum(tall) - gap * (len(rows) - 1)
    # A little of the slack goes into the rows and the rest stays white:
    # lanes stretched to fill an A3 are lanes that are mostly air, and a
    # foot of quiet paper is what a printed sheet wants anyway.
    tall = [h + max(0.0, min(over, 8.0 * len(rows))) / len(rows)
            for h in tall]
    body: list = []
    at: dict = {}
    y = top
    for row, height in zip(rows, tall):
        for box in row:
            box.y, box.h = y, height
            at[box.key] = box
            body += _lane(box)[0]
        y += height + gap

    # The spine: sideways between neighbours, and by elbow between rows,
    # with the three backends fed from one bus under the core so that
    # three arrows do not cross the page as three diagonals.
    bus = at["core"].y + at["core"].h + gap / 2
    body += _arrow([(at["core"].x + at["core"].w / 2, at["core"].y
                     + at["core"].h), (at["core"].x + at["core"].w / 2, bus),
                    (at["music"].x + at["music"].w / 2, bus)])
    for a, b, what, _via in SPINE:
        one, two = at.get(a), at.get(b)
        if one is None or two is None:
            continue
        if abs(one.y - two.y) < 0.01:                    # side by side
            left, right = sorted((one, two), key=lambda b: b.x)
            at_y = min(one.y + one.h - 4.0,
                       max(one.used, two.used) + one.y + 7.0)
            head = (two.x - 1.2, at_y) if two is right else \
                (two.x + two.w + 1.2, at_y)
            tail = (one.x + one.w + 0.4, at_y) if one is left \
                else (one.x - 0.4, at_y)
            body += _arrow([tail, head], what, above=at_y)
        elif one.key == "core":                          # off the bus
            mid = two.x + two.w / 2
            body += _arrow([(mid, bus), (mid, two.y - 1.2)], what, turn=True)
        else:                                            # a plain drop
            mid = min(one.x + one.w, two.x + two.w) - 14
            body += _arrow([(mid, one.y + one.h + 0.4), (mid, two.y - 1.2)],
                           what, turn=True)

    head = [
        f'<text class="title" x="{MARGIN:.2f}" y="{MARGIN + 8:.2f}">'
        'gestate — the whole thing on one sheet</text>',
        f'<text class="subtitle" x="{MARGIN:.2f}" y="{MARGIN + 14.5:.2f}">'
        + _ticked("A language that describes music, pictures and sound, and "
                  "the host that performs what it describes.  Generated by "
                  "`python -m gestate.atlas` — every box is a file that "
                  "exists and every arrow an import that is there.")
        + '</text>',
        f'<text class="foot" x="{MARGIN:.2f}" y="{PAGE_H - MARGIN + 2:.2f}">'
        + _ticked("Lanes and spine are declared in `gestate/atlas.py`; "
                  "modules, libraries and crates are read from the tree.  "
                  "`test_atlas.py` fails when this sheet is not what the "
                  "source renders — then run the command above.")
        + '</text>',
    ]

    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W:.0f}mm" '
        f'height="{PAGE_H:.0f}mm" viewBox="0 0 {PAGE_W:.0f} {PAGE_H:.0f}">',
        "<!-- Generated by `python -m gestate.atlas`. Do not edit by hand. -->",
        "<defs>",
        '<marker id="tip" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="5" markerHeight="5" orient="auto-start-reverse">',
        '<path d="M 0 1 L 9 5 L 0 9 z" fill="#3b4a55"/>',
        "</marker>",
        "</defs>",
        "<style>",
        "  text { font-family: 'DejaVu Sans', Verdana, sans-serif;"
        " fill: #22303a; }",
        "  .mono, .chiptext { font-family: 'DejaVu Sans Mono',"
        " Consolas, monospace; }",
        "  .title { font-size: 7.4px; font-weight: 700; }",
        "  .subtitle { font-size: 3.1px; fill: #55646e; }",
        "  .foot { font-size: 2.7px; fill: #6b7982; }",
        "  .lane { stroke: #c9d2d8; stroke-width: 0.35; }",
        "  .lanetitle { font-size: 4.6px; font-weight: 700; }",
        "  .note { font-size: 2.9px; fill: #4a5860; }",
        "  .extra { font-size: 2.9px; fill: #3b4a55; }",
        "  .chip { fill: #ffffff; stroke: #b9c4cc; stroke-width: 0.3; }",
        "  .chiptext { font-size: 2.7px; text-anchor: middle; }",
        "  .edge { stroke: #3b4a55; stroke-width: 0.55; fill: none; }",
        "  .edgetext { font-size: 2.7px; fill: #3b4a55; text-anchor: middle; }",
        "</style>",
        f'<rect x="0" y="0" width="{PAGE_W:.0f}" height="{PAGE_H:.0f}" '
        'fill="#ffffff"/>',
        *head,
        *body,
        "</svg>",
        "",
    ])


# ---------------------------------------------------------------------------
# Writing it, and saying when it is behind
# ---------------------------------------------------------------------------

def generate(root=None) -> dict:
    """Sheet name → its text.  One for now; the shape takes more."""
    root = Path(root) if root is not None else Path(__file__).parent.parent
    return {"whole.svg": render(root)}


def write(root=None) -> list:
    """Write the sheets that changed, and say which."""
    root = Path(root) if root is not None else Path(__file__).parent.parent
    out = root / "doc" / "atlas"
    out.mkdir(parents=True, exist_ok=True)
    changed = []
    for name, text in generate(root).items():
        target = out / name
        if not target.exists() or target.read_text() != text:
            target.write_text(text)
            changed.append(name)
    return changed


def stale(root=None) -> list:
    """Which sheets are behind the source — what `--check` reports."""
    root = Path(root) if root is not None else Path(__file__).parent.parent
    out = root / "doc" / "atlas"
    return [name for name, text in generate(root).items()
            if not (out / name).exists() or (out / name).read_text() != text]


#: How a `.svg` becomes a `.png`, best first.  **A picture nobody can
#: look at is not much of a picture**: the sheet is checked by a test
#: and read by a person, and the person may be reading it in a terminal,
#: over a wire, or through an assistant that can open a raster and not a
#: vector.  So the run makes both.
#:
#: `cairosvg` first because it is a `pip install` into the same
#: interpreter the suite runs under — no root, no application, about a
#: second — and it renders this sheet identically to Inkscape, CSS
#: classes and all.  The rest are what a machine might happen to have;
#: Inkscape is last because it is a whole editor being asked to convert
#: a file, and it takes two and a half seconds to say so.
RASTERISERS: list[tuple[str, list]] = [
    ("rsvg-convert", ["rsvg-convert", "-w", "{w}", "-o", "{png}", "{svg}"]),
    ("resvg", ["resvg", "--width", "{w}", "{svg}", "{png}"]),
    ("inkscape", ["inkscape", "--export-type=png", "--export-width={w}",
                  "--export-filename={png}", "{svg}"]),
]


def rasterise(svg: Path, png: Path, width: int = 1820) -> str:
    """Write `png` from `svg`, and say which tool did it.

    Returns the empty string when nothing on this machine can — which
    is not an error: the SVG is the artefact, the PNG is a convenience,
    and a build that failed because a *convenience* was missing would
    be the tail wagging the dog.  `tools/toolbox.sh` says what to
    install.
    """
    import shutil
    import subprocess

    try:
        import cairosvg

        cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=width)
        return "cairosvg"
    except ImportError:
        pass
    for name, argv in RASTERISERS:
        if shutil.which(argv[0]) is None:
            continue
        line = [a.format(w=width, png=png, svg=svg) for a in argv]
        if subprocess.run(line, capture_output=True, check=False).returncode == 0:
            return name
    return ""


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.atlas",
        description="Draw the project's architecture from the source.")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit non-zero if doc/atlas/ is behind")
    ap.add_argument("--no-png", action="store_true",
                    help="write only the .svg, not the .png beside it")
    ap.add_argument("--width", type=int, default=1820,
                    help="the .png's width in pixels (default 1820, "
                         "about 110 dpi at A3)")
    args = ap.parse_args(argv)

    root = Path(__file__).parent.parent
    told = unplaced(root) + phantom(root) + unproven(root) + missing_files(root)
    if told:
        print("the atlas is out of step with the tree:")
        for line in told:
            print(f"  {line}")
        return 1
    if args.check:
        behind = stale(root)
        if behind:
            print("doc/atlas/ is out of date: " + ", ".join(behind))
            print("run `python -m gestate.atlas`")
            return 1
        print("doc/atlas/ is up to date")
        return 0
    changed = write(root)
    print(f"wrote {len(changed)} sheet(s)"
          + (": " + ", ".join(changed) if changed else " — nothing to do"))
    if args.no_png:
        return 0
    # **Every sheet, not only the ones that changed.**  A `.png` can be
    # missing while its `.svg` is current — a fresh clone has neither,
    # and the raster is not committed — so this is asked of the sheets
    # rather than of the diff.
    out = root / "doc" / "atlas"
    for name in sorted(generate(root)):
        svg = out / name
        png = svg.with_suffix(".png")
        by = rasterise(svg, png, args.width)
        if by:
            print(f"  {png.name} — {png.stat().st_size / 1024:.0f}K, by {by}")
        else:
            print(f"  {png.name} — no rasteriser; `tools/toolbox.sh` says "
                  "what to install")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
