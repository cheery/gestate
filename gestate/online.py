"""A `.ges` file as a page that plays it — `card:online.md`, piece B.

    python -m gestate.online examples/audio/twinkle.ges -o site/

Writes a directory a static host can serve as it is: the page, the
player, the worklet, the graph as a `.wasm` (`audiowasm.build`) and a
`.json` beside it carrying what the worklet needs to drive the module
the way `audiollvm.native_blocks` drives the `.so` — the state size,
the slot layout, and the score already baked to slot changes at
128-frame boundaries, because 128 is the worklet's quantum and
`scored` delivers on the block the caller names.

**The browser computes the sound; the only server is a file host**
(`card:online.md` §"Questions", 2).  So nothing here runs at request
time: no Python in the page, no process behind it.  What the page does
is the vision's first two verbs — open a file, hear it — and the
source is shown read-only; *change it* is piece C, and this file does
not pretend otherwise.

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

from . import audioperform, audiowasm

#: The worklet's render quantum, which is what the schedule is baked on.
QUANTUM = 128
RATE = 44100

#: complaint  world — a page cannot be written where the tools are not (audiowasm says which)


class OnlineError(Exception):
    """The generator refusing, with the reason."""


def _control(src: str, graph, rate: int = RATE):
    """`(control, duration)` — the desk's own control function for the
    file, and how long the piece is in frames.  Shared with the test so
    the comparison drives both renders through one reading."""
    from .audioscore import unfolding_names

    perf = audioperform.Performance(graph)
    duration = int(30 * rate)
    if audioperform.has_score(src):
        if unfolding_names(src):
            #: complaint  author, nowhere — a score that unfolds forever cannot be baked to a file; a page for one is a performer in the browser, which is piece C's question
            raise OnlineError("this score unfolds, and a page carries a "
                              "score baked to its end — the piece that "
                              "unfolds forever is not this page's yet")
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
        "changes": changes,
    }


def generate(path, out, rate: int = RATE) -> Path:
    """Write the page for `path` into `out` and return the directory."""
    why = audiowasm.missing()
    if why is not None:
        raise OnlineError(why)
    path, out = Path(path), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    src = path.read_text()
    graph = audioperform.graph_of(src, rate=rate)
    stem = path.stem
    wasm = audiowasm.build(graph, out)
    wasm.replace(out / f"{stem}.wasm")
    for stray in out.glob("synth*"):
        stray.unlink()
    data = bake(src, graph, rate)
    data["imports"] = [n for _, n in audiowasm.imports_of(out / f"{stem}.wasm")]
    (out / f"{stem}.json").write_text(json.dumps(data, separators=(",", ":")))
    here = Path(__file__).parent
    shutil.copyfile(here / "online.js", out / "player.js")
    shutil.copyfile(here / "online-worklet.js", out / "worklet.js")
    page = (here / "online.html").read_text()
    page = (page.replace("{{name}}", path.name)
                .replace("{{stem}}", stem)
                .replace("{{source}}", src.replace("&", "&amp;")
                                          .replace("<", "&lt;")))
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
    try:
        out = generate(args.file, args.out, args.rate)
    except OnlineError as e:
        print(f"gestate.online: {e}", file=sys.stderr)
        return 2
    print(f"{out}/index.html — serve the directory as it is")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
