"""A `.ges` file as a page that plays it — `card:online.md`, piece B.

    python -m gestate.online examples/audio/twinkle.ges -o site/
    python -m gestate.online examples/audio -o site/     # every piece, and an index

Writes a directory a static host can serve as it is: the page, the
player, the worklet, the graph as a `.wasm` (`audiowasm.build`) and a
`.json` beside it carrying what the worklet needs to drive the module
the way `audiollvm.native_blocks` drives the `.so` — the state size,
the slot layout, and the score already baked to slot changes at
128-frame boundaries, because 128 is the worklet's quantum and
`scored` delivers on the block the caller names.

A score that **unfolds forever** is performed rather than baked — the
dynamic path, forced quantum by quantum for `WINDOW` seconds — and the
page says that what it carries is a window (`_control`, 2026-09-01).
A score that **listens** is still refused, with the reason: a tab has
no keyboard, and `hear holds.keys` with empty hands is silence.

**The browser computes the sound; the only server is a file host**
(`card:online.md` §"Questions", 2).  So nothing here runs at request
time: no Python in the page, no process behind it.  What the page does
is the vision's first two verbs — open a file, hear it — and, since
piece C2, the fourth for the knobs a file declares: a slider beside
each declaration writes the control slot while the piece plays
(`knobs` below).  *Change the text* is still piece C1, and this file
does not pretend otherwise.

**How it reaches the web** is `tools/pages.sh` — Henri's pick,
2026-08-29, R2 of the card's question 8: a `gh-pages` branch this
generator fills and he pushes now and then (`keeper.md`), because
*"tämän sivuston ei tarvitse olla tuore koko ajan"*.

**Generated, and checked.**  `test/test_online.py` generates this page
for an example and opens it in a headless Chrome, where the same
worklet renders through an `OfflineAudioContext` and the frames come
back for comparison with `run_native` — a real browser, the real
worklet, and the number is bit-identical after the one rounding the
browser owns (doubles to the output's floats).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import audioperform, audiowasm, webshell
from .notes import read

#: The worklet's render quantum, which is what the schedule is baked on.
QUANTUM = 128
RATE = 44100

#: What the picture sits on, and it is the plugin's own ground —
#: `shell/panel/src/panels.rs`'s `BG`, which is what
#: `Panel::render_into` clears to before the canvas is drawn over it.
#:
#: **A picture is composed against this and not against a page.**  Every
#: one of the six was drawn by somebody looking at the plugin's window,
#: so a substrate leaves the ground showing wherever it means to — and
#: on white that reads as a hole rather than as a background (Henri,
#: 2026-09-04, on `lantern.ges`: *"shows against a white background and
#: it seems a bit ugly that way"*).  Repeated here rather than imported
#: because Rust constants do not cross; `test_online.py` holds the two
#: equal.
CANVAS_BG = "#14161a"

#: The box the picture is drawn in, and the origin is its centre — which
#: is where `gui.py` puts `cx, cy` and therefore where every one of these
#: substrates was composed around.  **A picture wider or taller than this
#: is cropped in silence**, so `test_online.py` measures all six against
#: it rather than trusting that today's fit is tomorrow's.
CANVAS_W, CANVAS_H = 480, 320

#: How many points a scope's trace crosses as, and it is
#: `audioeditor.Workbench.TRACE_POINTS` — the window downsampled by
#: **max-absolute per bucket**, because a scope that averages away a
#: click is a scope that lies (`spec/scope.md`).  The number is repeated
#: rather than imported because the editor is a desk program the page
#: does not otherwise depend on; `test_online.py` holds the two equal.
TRACE_POINTS = 128

#: Seconds a page carries when nothing in the file says when the piece
#: ends — a synth with no score at all, and (since 2026-09-01) a score
#: that unfolds forever.  The terminal's answer to the same question is
#: `--seconds`, which a page has nobody to ask.
WINDOW = 30

#: complaint  world — a page cannot be written where the tools are not (audiowasm says which)


class OnlineError(Exception):
    """The generator refusing, with the reason."""


def _control(src: str, graph, rate: int = RATE):
    """`(control, duration)` — the desk's own control function for the
    file, and how long the piece is in frames.  Shared with the test so
    the comparison drives both renders through one reading.

    **A score that unfolds is performed, not baked to its end** — the
    dynamic path (`audioperform.dynamic`), forced quantum by quantum
    for `WINDOW` seconds and written down as the changes it made.
    That is the same routing the terminal does for `--dynamic`, with
    the page's own answer to *how long*: the terminal asks for
    `--seconds` and a page has nobody to ask.  What the page carries is
    then a **window**, not the piece, and it says so (`bake`'s
    `unfolds`).  Deterministic across two forcings at one seed, which
    is what lets the gate render the same thing twice and compare
    (measured on all five, 2026-09-01).
    """
    from .audioscore import heard_banks, unfolding_names

    perf = audioperform.Performance(graph)
    duration = int(WINDOW * rate)
    if audioperform.has_score(src):
        if unfolding_names(src):
            heard = heard_banks(src)
            if heard:
                #: complaint  author, nowhere — a score that plays what a keyboard holds has nothing to play in a tab with no keyboard; MIDI in the browser is not this page's yet
                raise OnlineError(
                    "this piece plays what your hands hold — `hear "
                    "holds." + sorted(heard)[0] + "` — and empty hands "
                    "are silence, so a tab with no keyboard has nothing "
                    "to play")
            performer, _ = audioperform.dynamic(src, rate=rate,
                                                block=QUANTUM,
                                                patience=None)
            perf.sources.append(audioperform.from_performer(performer))
        else:
            schedule, samples, _ = audioperform.scored(src, rate=rate,
                                                       block=QUANTUM)
            perf.sources.append(audioperform.from_schedule(schedule))
            duration = samples
    return perf.control(), duration


def bake(src: str, graph, rate: int = RATE) -> dict:
    """What the worklet needs, as plain data.

    `changes` is every control slot's value at every quantum boundary
    where it differs from the previous one, sampled through the same
    `Performance.control` the desk renders with — so the page and
    `run_native(..., block=128)` see the same value at the same `t`, by
    construction rather than by a second reading of the schedule.
    """
    from .audiollvm import _slots, out_channels
    from .audioscore import unfolding_names

    control, duration = _control(src, graph, rate)
    sources = graph.control_sources()
    changes, last = [], {}
    for t in range(0, duration, QUANTUM):
        for slot, node in enumerate(sources):
            value = control(node.id, t)
            value = float(value) if node.type_ == "Float" else int(value)
            if last.get(slot) != value:
                last[slot] = value
                changes.append([t, slot, value])
    return {
        "rate": rate,
        "quantum": QUANTUM,
        "channels": out_channels(graph),
        "stateBytes": 8 * (1 + sum(_slots(graph, n) for n in graph.nodes)),
        "slots": max(1, len(sources)),
        "types": [n.type_ for n in sources],
        "duration": duration,
        # The names that make this score endless, or `[]` — what the
        # page says instead of pretending `duration` is the piece.
        "unfolds": unfolding_names(src) if audioperform.has_score(src) else [],
        "changes": changes,
    }


def blurb(src: str) -> str:
    """The file's first comment line, after the `#` — what the index
    says beside the name.  Empty when the file opens with code."""
    for line in src.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
        if line:
            return ""
    return ""


def generate_site(directory, out, rate: int = RATE) -> tuple:
    """Every `.ges` under `directory` as a page, and an index — `(made,
    refused)`, the second as `(name, reason)` pairs.  A piece the
    generator refuses (one whose score listens for a keyboard) is left
    out of the index rather than failing the site: one piece's limit is
    not the others'."""
    directory, out = Path(directory), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    made, refused = [], []
    for path in sorted(directory.glob("*.ges")):
        try:
            generate(path, out / path.stem, rate, up=True)
        except OnlineError as e:
            refused.append((path.name, str(e)))
            shutil.rmtree(out / path.stem, ignore_errors=True)
            continue
        made.append((path.name, blurb(read(path))))
    # **Once, at the root, and only if anything drew** — the canvas
    # driver is the same program for every page and only the substrate
    # it is handed differs, so it is shared; but a gallery of pieces
    # that draw nothing must not carry 221 KB nobody fetches.  A page
    # that wanted it and could not have it says so itself
    # (`canvasSkipped`).
    if any((out / Path(name).stem / "canvas.js").exists() for name, _ in made):
        webshell.build(out)
    here = Path(__file__).parent
    items = "\n".join(
        f'<li><a href="{Path(name).stem}/">{name}</a>'
        + (f' <span>— {_escape(text)}</span>' if text else "") + "</li>"
        for name, text in made)
    page = (here / "online-index.html").read_text()
    (out / "index.html").write_text(page.replace("{{items}}", items)
                                        .replace("{{count}}", str(len(made))))
    # Pages runs Jekyll over a branch unless told not to, and Jekyll
    # drops files it has opinions about; this file is the telling.
    (out / ".nojekyll").write_text("")
    return made, refused


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;")


def knobs(src: str, graph, sites) -> list:
    """The knobs the file declares, as the page draws them — piece C2.

    **The workbench's own reading of a knob, not the card's first
    words.**  `card:online.md` §"The pieces" said *every literal is a
    knob*; in this tree a literal is folded into the step that consumes
    it on purpose (`audioextract._fold_constants`), and a knob is a
    control source the author declared — `40 ::: mkSig (wait
    pitchChan)` — which `audiospans.sites` places at its declaration
    and `audioeditor` draws beside it.  The page does what the window
    does, with the same three rules taken from it: a bank's channels
    are not knobs (a slider fighting the score would be a control that
    does nothing you can predict); the range follows the channel's
    type; and it is stretched to hold what the program declared
    (`fixme.md` F147 — `415 ::: mkSig` means 415).

    Each entry: `slot` into the worklet's control block, `name`,
    `line` in the author's file, `type`, `init`, `low`, `high`.
    """
    from .audioeditor import KNOB_RANGE, KNOB_RANGE_FLOAT
    from .audiovoices import banks_of, channels_of

    try:
        owned = {c for b in banks_of(src) for row in channels_of(src, b)
                 for c in row}
    except Exception:                                   # noqa: BLE001
        owned = set()
    slot_of = {n.id: i for i, n in enumerate(graph.control_sources())}
    out = []
    for site in sorted(sites, key=lambda s: (s.line, s.column)):
        if not site.is_control or site.path is not None:
            continue
        node = graph.node(site.node)
        if getattr(node, "chan", None) in owned:
            continue
        init = getattr(node, "init", None)
        low, high = KNOB_RANGE_FLOAT if node.type_ == "Float" else KNOB_RANGE
        if isinstance(init, (int, float)):
            low, high = min(low, init), max(high, init)
        out.append({"slot": slot_of[site.node], "name": site.name,
                    "line": site.line, "type": node.type_,
                    "init": init, "low": low, "high": high})
    return out


#: The eight bands `gestate/host.c` reports, by the names a file
#: declares to switch the filter bank on (`examples/audio/spectrum.ges`:
#: *a program that does not declare these channels is not charged for
#: it*).  The page keeps that bargain — the worklet runs the bank only
#: when one of these is in the substrate's channel list.
BANDS = tuple(f"band{k}" for k in range(8))


def canvas_of(src: str, graph, rate: int = RATE) -> dict | None:
    """The substrate a page draws beside the sound, or `None` — piece
    `clap.gui` of `card:audiovisual-gallery.md`.

    **The same payload a plugin gets.**  `export.substrate_of` writes
    the serialized second program, the constructor tags the walk decodes
    cells with, and the channel names in declaration order; `shell/web`
    opens exactly that, and `test_gallery.py` already holds the picture
    it draws equal to `gestate/gui.py`'s.  Nothing here reads a
    substrate or decides what one means.

    **And `meters` is what the instrument owes the picture.**  Six
    pieces declare a canvas and three of them are pictures *of the
    sound*: `spectrum` reads eight bands, a `peak` is a meter, and a
    `scope`'s trace is the window the ring already holds.  On the desk
    those arrive once a frame from `audioeditor.Editor` — `peak` from
    the transport, the bands from `host.c`'s filter bank, a trace from
    the engine's own ring.  A page has no such host, so the worklet
    computes them beside the sound it is already rendering and the
    main thread writes them to the canvas.  What is listed here is only
    **what this file declared**, which is the bargain each of those
    readings is offered under.
    """
    from .export import _BEAT_CHANS, bank_channels, substrate_of

    banked = bank_channels(src)
    knobs = frozenset(n.chan for n in graph.control_sources()
                      if n.chan not in banked and n.chan not in _BEAT_CHANS)
    sub = substrate_of(src, rate, graph, knobs)
    if sub is None:
        return None
    declared = set(sub["chans"])
    return {
        "text": sub["text"], "entry": sub["entry"],
        "tags": sub["tags"], "chans": sub["chans"],
        "meters": {
            "peak": "peak" in declared,
            # Which bands, not how many: a file may declare `band0` and
            # `band7` and nothing between, and the bank costs the same.
            "bands": [k for k, name in enumerate(BANDS) if name in declared],
            # A scope whose label is a channel this canvas declared.  The
            # index is the `read_scope_<i>` the module exports, in the
            # order `graph.scopes()` gives — which is the order
            # `audiollvm._read_scopes` numbered them in.
            "scopes": [{"label": label, "length": length, "index": i,
                        "points": TRACE_POINTS}
                       for i, (label, length, _node)
                       in enumerate(graph.scopes())
                       if label in declared],
        },
    }


def _source_html(src: str, knobs: list) -> str:
    """The file, one `<div>` a line, with a slider on the line that
    declares a knob — beside its own declaration, the way the window
    draws it, so a person reads the number and the knob together."""
    by_line: dict = {}
    for k in knobs:
        by_line.setdefault(k["line"], []).append(k)
    rows = []
    for i, text in enumerate(src.splitlines(), 1):
        row = f'<div class="ln" data-line="{i}">{_escape(text) or " "}'
        for k in by_line.get(i, ()):
            step = "any" if k["type"] == "Float" else "1"
            value = k["init"] if k["init"] is not None else k["low"]
            row += (f'<label class="knob"><span class="knob-name">'
                    f'{_escape(k["name"])}</span>'
                    f'<input type="range" data-slot="{k["slot"]}" '
                    f'data-type="{k["type"]}" min="{k["low"]}" '
                    f'max="{k["high"]}" step="{step}" value="{value}">'
                    f'<output>{value}</output></label>')
        rows.append(row + "</div>")
    return "\n".join(rows)


def generate(path, out, rate: int = RATE, up: bool = False) -> Path:
    """Write the page for `path` into `out` and return the directory.
    `up` adds the link back to an index one level above."""
    from .audiospans import located

    why = audiowasm.missing()
    if why is not None:
        raise OnlineError(why)
    path, out = Path(path), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    src = read(path)
    # The same graph `audioperform.graph_of` builds, with its nodes
    # placed in the file — one analysis, not two (`audiospans.located`).
    sites, graph = located(src, rate=rate)
    stem = path.stem
    wasm = audiowasm.build(graph, out)
    wasm.replace(out / f"{stem}.wasm")
    for stray in out.glob("synth*"):
        stray.unlink()
    data = bake(src, graph, rate)
    data["imports"] = [n for _, n in audiowasm.imports_of(out / f"{stem}.wasm")]
    data["knobs"] = knobs(src, graph, sites)
    # **The picture, when the file draws one and this machine can build
    # the shell.**  A toolchain the page generator lacks costs the piece
    # its canvas and nothing else — the sound is a different module and
    # was linked before we got here — so this is a skip with the reason
    # kept, not a refusal of the page (`generate_site` prints them).
    canvas = canvas_of(src, graph, rate)
    if canvas is not None:
        why = webshell.missing()
        if why is None:
            # One module for the whole gallery: written at the site root
            # by `generate_site`, and beside the page when there is no
            # root to share.  `webshell` says why.
            if not up:
                webshell.build(out)
            data["canvas"] = {**canvas,
                              "wasm": ("../" if up else "") + webshell.NAME}
        else:
            data["canvasSkipped"] = why
    (out / f"{stem}.json").write_text(json.dumps(data, separators=(",", ":")))
    here = Path(__file__).parent
    shutil.copyfile(here / "online.js", out / "player.js")
    shutil.copyfile(here / "online-worklet.js", out / "worklet.js")
    # Only for a piece that draws — `player.js` imports it dynamically,
    # so 45 of the site's 50 pages carry neither the file nor the fetch.
    if "canvas" in data:
        shutil.copyfile(here / "online-canvas.js", out / "canvas.js")
    page = (here / "online.html").read_text()
    page = (page.replace("{{name}}", path.name)
                .replace("{{stem}}", stem)
                .replace("{{source}}", _source_html(src, data["knobs"]))
                .replace("{{up}}", '<a href="../">all pieces</a> · ' if up else "")
                .replace("{{ground}}", CANVAS_BG)
                .replace("{{cw}}", str(CANVAS_W))
                .replace("{{ch}}", str(CANVAS_H)))
    (out / "index.html").write_text(page)
    return out


def main(argv=None) -> int:
    import argparse
    import sys

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("-o", "--out", default="site")
    ap.add_argument("--rate", type=int, default=RATE)
    args = ap.parse_args(argv)
    if Path(args.file).is_dir():
        made, refused = generate_site(args.file, args.out, args.rate)
        for name, why in refused:
            print(f"  left out: {name} — {why}", file=sys.stderr)
        print(f"{args.out}/index.html — {len(made)} pieces, "
              f"{len(refused)} left out; serve the directory as it is")
        return 0
    try:
        out = generate(args.file, args.out, args.rate)
    except OnlineError as e:
        print(f"gestate.online: {e}", file=sys.stderr)
        return 2
    print(f"{out}/index.html — serve the directory as it is")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
