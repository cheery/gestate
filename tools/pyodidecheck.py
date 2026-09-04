#!/usr/bin/env python3
#: asked-by: Henri, 2026-08-29 - "Olisiko C1 mittaus ja sitten lopetellaan?"
"""tools/pyodidecheck.py — seconds per change: the front end under Pyodide, in a real Chrome.

    python tools/pyodidecheck.py                       # twinkle, four edits
    python tools/pyodidecheck.py examples/audio/bell.ges

**The answer this measured is struck, 2026-09-04.**  Henri, at the
terminal: *"strike out the C1 choice so that it's not proposed
anymore"* — *"or precisely, the pyodide choice."*  **No Python runtime
runs in a gestate page**, and this file is the evidence for a decision
rather than a route to one: if you are reading it while looking for a
way to put the front end in a browser, the answer is
`card:online.md` §"The pieces", C1, and the direction the tree took
instead is `card:audiovisual-gallery.md` — the tree's own artefacts
compiled for `wasm32`, 221 KB with no imports, against the 10 MB this
tool loads.  It is kept because a refusal carrying its numbers is worth
more than the refusal, and it still runs.

`card:online.md` piece C1 asks one number before anything is built:
how long a *change* to a file costs when gestate's own Python front end
(parse → typecheck → extract → emit) runs in the browser.  This zips
`gestate/`, serves it with a page that loads Pyodide from jsdelivr,
runs `graph_of` + `emit` on the file and on three one-number edits of
it, and prints what the browser measured beside the same run native.
The first edit is cold (imports, caches); the next three are what a
person feels.  Needs Chrome and the network; the page POSTs its
numbers back, on the wall clock (`test/test_online.py` says why).

What it does not measure: the compile.  `emit` writes LLVM text and no
LLVM runs in a browser, so the number here is the front end alone —
the rest of C1 is an emitter that writes wasm bytes directly, and its
cost is being kept, not seconds.
"""

from __future__ import annotations

import http.server
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js"

PAGE = """<pre id="r">running</pre>
<script src="%s"></script>
<script>
const post = (s) => fetch("/log", {method: "POST", body: s});
(async () => {
  const t = {};
  try {
    let t0 = performance.now();
    const py = await loadPyodide();
    t.load_pyodide = (performance.now() - t0) / 1000;
    t0 = performance.now();
    py.unpackArchive(await (await fetch("gestate.zip")).arrayBuffer(), "zip");
    py.globals.set("src", await (await fetch("piece.ges")).text());
    py.globals.set("edits_json", await (await fetch("edits.json")).text());
    t.unpack = (performance.now() - t0) / 1000;
    const r = await py.runPythonAsync(`
import json, time
r = {}
t0 = time.perf_counter()
from gestate import audioperform, audiollvm
r["import"] = time.perf_counter() - t0
texts = [src] + [src.replace(a, b) for a, b in json.loads(edits_json)]
for i, text in enumerate(texts):
    t0 = time.perf_counter()
    g = audioperform.graph_of(text, rate=44100)
    audiollvm.emit(g, wants=("render_block",))
    r[f"change_{i}"] = time.perf_counter() - t0
json.dumps(r)
`);
    await post("result " + JSON.stringify({...t, ...JSON.parse(r)}));
  } catch (e) { await post("fail " + e + "\\n" + (e.stack || "")); }
})();
</script>
"""

#: One-number edits a person would make, as (old, new) — applied when
#: the text has the old; an edit that does not apply is the same text
#: again and shows up as a cache hit, which is why three are tried.
EDITS = [("gain 0.3", "gain 0.4"), ("bpm = 100", "bpm = 96"),
         ("Adsr 0.01 0.2", "Adsr 0.02 0.2")]


class _Handler(http.server.SimpleHTTPRequestHandler):
    result: list = []
    arrived = threading.Event()

    def log_message(self, *_):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        _Handler.result.append(self.rfile.read(n).decode())
        self.send_response(204)
        self.end_headers()
        _Handler.arrived.set()


def native(src: str) -> dict:
    from gestate import audiollvm, audioperform

    out = {}
    texts = [src] + [src.replace(a, b) for a, b in EDITS]
    for i, text in enumerate(texts):
        t0 = time.perf_counter()
        g = audioperform.graph_of(text, rate=44100)
        audiollvm.emit(g, wants=("render_block",))
        out[f"change_{i}"] = time.perf_counter() - t0
    return out


def main(argv=None) -> int:
    piece = Path(argv[0]) if argv else ROOT / "examples" / "audio" / "twinkle.ges"
    chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser")
                   if shutil.which(c)), None)
    if chrome is None:
        print("no Chrome to open the page in")
        return 2
    src = piece.read_text()
    with tempfile.TemporaryDirectory() as d:
        site = Path(d) / "site"
        site.mkdir()
        with zipfile.ZipFile(site / "gestate.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for p in (ROOT / "gestate").rglob("*"):
                if p.suffix in (".py", ".ges") and "__pycache__" not in p.parts:
                    z.write(p, p.relative_to(ROOT))
        (site / "piece.ges").write_text(src)
        (site / "edits.json").write_text(json.dumps(EDITS))
        (site / "index.html").write_text(PAGE % PYODIDE)
        handler = lambda *a, **k: _Handler(*a, directory=str(site), **k)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{server.server_address[1]}/index.html"
        proc = subprocess.Popen(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             f"--user-data-dir={d}/profile", url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            ok = _Handler.arrived.wait(timeout=180)
        finally:
            proc.kill()
            proc.wait()
            server.shutdown()
    if not ok:
        print("the page never answered — no network for Pyodide, or Chrome did not load it")
        return 1
    line = _Handler.result[0]
    if line.startswith("fail"):
        print(line)
        return 1
    browser = json.loads(line[len("result "):])
    desk = native(src)
    print(f"{piece.name}: Pyodide loads in {browser['load_pyodide']:.1f}s, "
          f"gestate unpacks in {browser['unpack']:.2f}s, imports in {browser['import']:.2f}s")
    print(f"{'change':>10} {'browser':>9} {'native':>9}")
    for i in range(len(EDITS) + 1):
        k = f"change_{i}"
        tag = "cold" if i == 0 else f"edit {i}"
        print(f"{tag:>10} {browser[k]:>8.2f}s {desk[k]:>8.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
