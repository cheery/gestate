"""The generated page plays what the desk plays — `card:online.md`, piece B.

`gestate.online.generate` writes a directory; this serves it from a
thread, opens it in a **headless Chrome** with `?check=N`, and reads
the frames the page's own worklet rendered through an
`OfflineAudioContext` back out of the DOM.  Compared with `run_native`
at the worklet's quantum after the one rounding the browser owns —
doubles into the output's floats — they are identical.  A page that
loaded, compiled, instantiated and rendered in a real browser is the
claim; a test of the JSON alone would be a test of the generator's
opinion of itself.

A score that unfolds forever is carried as a *window* — performed
through the dynamic path for `online.WINDOW` seconds — and the same
comparison holds it, which works only because two forcings of one
endless score at one seed agree (held below, and by the browser case
on `lantern.ges`).

Skips, naming the tool, without `clang`/`wasm-ld` or a Chrome.
"""

from __future__ import annotations

import http.server
import json
import shutil
import struct
import subprocess
import tempfile
import threading
from pathlib import Path

import pytest

from gestate import audiowasm, online, webshell

AUDIO_DIR = Path(__file__).resolve().parents[1] / "examples" / "audio"
FRAMES = 44100                             # a second: past the first note change

CHROME = next((c for c in ("google-chrome", "chromium", "chromium-browser",
                           "google-chrome-stable") if shutil.which(c)), None)

needs_tools = pytest.mark.skipif(audiowasm.missing() is not None,
                                 reason=audiowasm.missing() or "")
needs_chrome = pytest.mark.skipif(CHROME is None,
                                  reason="no Chrome to open the page in")


class _Site(http.server.SimpleHTTPRequestHandler):
    """Serves the directory, and takes the one POST the page's check
    mode makes — the frames — into `result`."""
    result: list = []
    arrived = threading.Event()

    def log_message(self, *_):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        _Site.result.append(self.rfile.read(n).decode())
        self.send_response(204)
        self.end_headers()
        _Site.arrived.set()


def _serve(directory: Path):
    handler = lambda *a, **k: _Site(*a, directory=str(directory), **k)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def _rendered(site: Path, frames: int, query: str = "") -> list:
    """Open the page's check mode in a headless Chrome and wait for the
    frames it POSTs back; `query` is more of the page's URL, `&set=…`
    for a knob turned first.  Wall clock, not `--virtual-time-budget`: an
    OfflineAudioContext does not render to its end under virtual time,
    which cost an hour on 2026-08-29 to find out."""
    _Site.result.clear()
    _Site.arrived.clear()
    server, base = _serve(site)
    # Its own profile directory, or the command hands the URL to a Chrome
    # already open on the desktop and exits at once — which is what a page
    # that "never loaded" was on 2026-08-29.  No `--dump-dom`: that mode
    # quits about a second after load, before a render this long has
    # posted; a plain headless browser stays up until it is killed here.
    profile = tempfile.mkdtemp(prefix="gestate-chrome")
    chrome = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--user-data-dir={profile}",
         f"{base}/index.html?check={frames}&to=/check{query}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ok = _Site.arrived.wait(timeout=60)
    finally:
        chrome.kill()
        chrome.wait()
        server.shutdown()
        shutil.rmtree(profile, ignore_errors=True)
    assert ok, "the page never posted its frames — it did not load, or did not render"
    return [[float(x) for x in line.split()]
            for line in _Site.result[0].strip().split("\n") if line]


def _as_float32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


@needs_tools
@needs_chrome
@pytest.mark.parametrize("name", ["twinkle.ges", "twoknobs.ges", "gyre.ges",
                                  "lantern.ges"])
def test_the_page_renders_in_a_browser_what_the_desk_renders(name):
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of

    with tempfile.TemporaryDirectory() as d:
        site = online.generate(AUDIO_DIR / name, Path(d) / "site")
        got = _rendered(site, FRAMES)

        src = (AUDIO_DIR / name).read_text()
        graph = graph_of(src, rate=online.RATE)
        control, _ = online._control(src, graph)
        want = run_native(graph, d, FRAMES, block=online.QUANTUM,
                          control=control)
    channels = len(got)
    assert len(got[0]) == FRAMES
    assert channels == graph.channels()
    for c in range(channels):
        frames = [w if channels == 1 else w[c] for w in want]
        off = [i for i, (a, b) in enumerate(zip(frames, got[c]))
               if _as_float32(a) != b]
        assert not off, (f"{name} channel {c}: first differing frame "
                         f"{off[0]}: desk {frames[off[0]]!r}, page {got[c][off[0]]!r}")
    assert max(abs(x) for x in got[0]) > 0, f"{name}: the page rendered silence"


@needs_tools
def test_the_generated_directory_is_what_a_host_serves():
    """No stray build products, and every file the page fetches is there
    under the name it fetches it by.

    **And nothing a piece does not need.**  `twinkle.ges` declares no
    substrate, so it carries neither `canvas.js` nor the picture's
    shell — `player.js` imports the first dynamically and only when the
    data says there is a canvas.  45 of the site's 50 pages are this
    piece, and 221 KB apiece is what the conditional is worth.
    """
    with tempfile.TemporaryDirectory() as d:
        site = online.generate(AUDIO_DIR / "twinkle.ges", d)
        names = sorted(p.name for p in site.iterdir())
    assert names == ["index.html", "player.js", "twinkle.json",
                     "twinkle.wasm", "worklet.js"]


@needs_tools
def test_a_directory_becomes_a_site_with_an_index_and_leaves_out_what_it_cannot():
    """Three files in: two pages and an index naming them with their
    first comment line; the unfolding one left out and reported, not
    fatal.  `.nojekyll` beside them, because the branch is served by
    Pages (`tools/pages.sh`)."""
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "pieces"
        src.mkdir()
        for name in ("twinkle.ges", "twoknobs.ges", "arpeggiator.ges"):
            shutil.copyfile(AUDIO_DIR / name, src / name)
        made, refused = online.generate_site(src, Path(d) / "site")
        site = Path(d) / "site"
        index = (site / "index.html").read_text()
        top = sorted(p.name for p in site.iterdir())
    assert [n for n, _ in made] == ["twinkle.ges", "twoknobs.ges"]
    assert [n for n, _ in refused] == ["arpeggiator.ges"] and "hands" in refused[0][1]
    assert top == [".nojekyll", "index.html", "twinkle", "twoknobs"]
    assert 'href="twinkle/"' in index and "Twinkle Twinkle Little Star" in index
    assert "arpeggiator" not in index


@needs_tools
def test_a_score_that_plays_what_hands_hold_is_refused_with_the_reason():
    """The one refusal left, and it is not about unfolding: a page has
    no keyboard, and `hear holds.keys` with empty hands is silence by
    design (`examples/audio/arpeggiator.ges`).  Baking thirty seconds
    of it measured 40 changes for 40 slots — every one an initial value
    — which is a page that plays nothing and says nothing about why."""
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(online.OnlineError, match="hands"):
            online.generate(AUDIO_DIR / "arpeggiator.ges", d)


def test_the_banks_a_score_listens_to_are_read_from_its_declarations():
    """`audioscore.heard_banks`, the detector behind that refusal —
    parsed and reachable from `score`, never text, the same rule
    `assigned_banks` is held to.  Three of the tree's fifty-three
    pieces name one, and they are exactly the three whose baked window
    measured silent."""
    from gestate.audioscore import heard_banks

    listening = {p.name for p in sorted(AUDIO_DIR.glob("*.ges"))
                 if heard_banks(p.read_text())}
    assert listening == {"arpeggiator.ges", "jazz.ges", "ladder.ges"}
    assert heard_banks((AUDIO_DIR / "arpeggiator.ges").read_text()) == {"keys"}
    assert heard_banks((AUDIO_DIR / "twinkle.ges").read_text()) == set()


@needs_tools
def test_a_score_that_unfolds_is_carried_as_a_window_that_says_so():
    """A score with no end is performed rather than baked, for
    `WINDOW` seconds, and the page says that is what it is — a piece
    that stops after thirty seconds without saying why reads as a bug.
    `lantern.ges` is `cycle`: endless by contract."""
    with tempfile.TemporaryDirectory() as d:
        site = online.generate(AUDIO_DIR / "lantern.ges", Path(d) / "site")
        data = json.loads((site / "lantern.json").read_text())
        page = (site / "index.html").read_text()
    assert data["unfolds"] == ["cycle"]
    assert data["duration"] == online.WINDOW * online.RATE
    beyond = [c for c in data["changes"] if c[0] > 0]
    assert len(beyond) > 20, "the window was baked, but nothing happens in it"
    assert 'id="unfolds"' in page, "the page has nowhere to say the piece goes on"


@needs_tools
def test_the_window_a_page_carries_is_the_same_window_twice():
    """The property the browser gate rests on.  A page's changes are
    forced once at generate time and the comparison forces them again
    for `run_native`, so two independent performances of one endless
    score at one seed have to agree — measured on all five, 2026-09-01,
    and held here on the cheapest of them."""
    from gestate.audioperform import graph_of

    src = (AUDIO_DIR / "spiral.ges").read_text()
    graph = graph_of(src, rate=online.RATE)
    once = online.bake(src, graph)["changes"]
    again = online.bake(src, graph)["changes"]
    assert once == again and len([c for c in once if c[0] > 0]) > 10


def _knobs(name: str) -> tuple:
    src = (AUDIO_DIR / name).read_text()
    from gestate.audiospans import located
    sites, graph = located(src, rate=online.RATE)
    return online.knobs(src, graph, sites), graph, src


def test_the_knobs_a_file_declares_are_baked_beside_their_lines():
    """Piece C2: the workbench's knobs, as data the page can draw — at
    the author's line, with the range the window would give them
    (`fixme.md` F147: stretched to the declared value), and none for a
    bank's channels, which the score writes."""
    got, _, src = _knobs("twoknobs.ges")
    lines = src.splitlines()
    assert [(k["name"], k["slot"], k["type"], k["init"], k["low"], k["high"])
            for k in got] == [("pitch", 0, "Int", 40, 0, 100),
                              ("cutoff", 1, "Int", 70, 0, 100)]
    assert lines[got[0]["line"] - 1].startswith("pitch = 40 :::")
    assert lines[got[1]["line"] - 1].startswith("cutoff = 70 :::")
    got, _, _ = _knobs("tuning.ges")
    assert [(k["name"], k["init"], k["high"]) for k in got] == [("reference", 415, 415)]
    got, graph, _ = _knobs("twinkle.ges")
    assert got == [] and len(graph.control_sources()) == 16, \
        "a voices bank's sixteen channels are the score's, not sliders"


@needs_tools
def test_the_page_draws_a_slider_on_the_line_that_declares_the_knob():
    with tempfile.TemporaryDirectory() as d:
        site = online.generate(AUDIO_DIR / "twoknobs.ges", d)
        page = (site / "index.html").read_text()
    row = next(l for l in page.splitlines() if 'data-line="32"' in l)
    assert "pitch = 40 ::: mkSig (wait pitchChan)" in row
    assert 'data-slot="0"' in row and 'min="0" max="100"' in row and 'value="40"' in row
    assert page.count('type="range"') == 2


@needs_tools
@needs_chrome
def test_a_knob_turned_on_the_page_is_what_the_desk_renders_at_that_value():
    """The postcondition of piece C2, in the browser: both knobs turned
    before the check, and the frames are the desk's under the same
    two values — not merely different from the untouched render."""
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of

    with tempfile.TemporaryDirectory() as d:
        site = online.generate(AUDIO_DIR / "twoknobs.ges", Path(d) / "site")
        got = _rendered(site, FRAMES, "&set=0:80,1:20")

        src = (AUDIO_DIR / "twoknobs.ges").read_text()
        graph = graph_of(src, rate=online.RATE)
        pitch, cutoff = (n.id for n in graph.control_sources())
        base, _ = online._control(src, graph)
        control = lambda node, t: {pitch: 80, cutoff: 20}.get(node, base(node, t))
        want = run_native(graph, d, FRAMES, block=online.QUANTUM, control=control)
        plain = run_native(graph, d, FRAMES, block=online.QUANTUM, control=base)
    assert len(got) == 1 and len(got[0]) == FRAMES
    off = [i for i, (a, b) in enumerate(zip(want, got[0])) if _as_float32(a) != b]
    assert not off, (f"first differing frame {off[0]}: desk {want[off[0]]!r}, "
                     f"page {got[0][off[0]]!r}")
    assert any(_as_float32(a) != _as_float32(b) for a, b in zip(want, plain)), \
        "turning both knobs changed nothing, so the check checked nothing"


@needs_tools
@needs_chrome
def test_a_knob_turned_while_the_page_plays_reaches_the_sound_on_the_port():
    """The other half of C2's postcondition — *while it plays*.  The
    offline context is suspended at a quantum boundary, the knobs are
    turned through the same port a playing page uses, and the render
    resumes; the desk's control switches at the same frame."""
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of

    at = 172 * online.QUANTUM                          # half a second, on a quantum
    with tempfile.TemporaryDirectory() as d:
        site = online.generate(AUDIO_DIR / "twoknobs.ges", Path(d) / "site")
        got = _rendered(site, FRAMES, f"&set=0:80,1:20&at={at}")

        src = (AUDIO_DIR / "twoknobs.ges").read_text()
        graph = graph_of(src, rate=online.RATE)
        pitch, cutoff = (n.id for n in graph.control_sources())
        base, _ = online._control(src, graph)
        control = lambda node, t: ({pitch: 80, cutoff: 20}.get(node, base(node, t))
                                   if t >= at else base(node, t))
        want = run_native(graph, d, FRAMES, block=online.QUANTUM, control=control)
    off = [i for i, (a, b) in enumerate(zip(want, got[0])) if _as_float32(a) != b]
    assert not off, (f"first differing frame {off[0]} (turned at {at}): "
                     f"desk {want[off[0]]!r}, page {got[0][off[0]]!r}")


# ── The picture, on the page — card:audiovisual-gallery.md, day two ─────────

#: The six pieces in `examples/audio/` that declare a substrate.  Kept
#: here rather than imported from `test_gallery.py` for that file's own
#: stated reason: neither test's helpers become the other's contract.
DRAWS = ["chopin.ges", "envelope.ges", "lantern.ges", "scoped.ges",
         "spectrum.ges", "substrate.ges"]

needs_shell = pytest.mark.skipif(webshell.missing() is not None,
                                 reason=webshell.missing() or "")

#: The page reads the display wire and posts it back in the grammar
#: `test_gallery.py` and `shell/panel/tests/*.display` both speak, so
#: the comparison is between two pictures and not two encodings.  Walked
#: in the page because that is where the module's memory is.
_WIRE_PROBE = """
<script type="module">
const post = (s) => fetch("/check", {method: "POST", body: s});
window.onerror = (m, s, l, c, e) => post("ERROR " + m + "\\n" + (e && e.stack));
window.addEventListener("unhandledrejection",
  (e) => post("REJECT " + e.reason + "\\n" + (e.reason && e.reason.stack)));
const rgb = (w) => `${(w >> 16) & 255} ${(w >> 8) & 255} ${w & 255}`;
setTimeout(() => {
  const p = window.gestatePicture;
  if (!p) return post("ERROR no picture on the page");
  const base = p.ex.web_display(p.w);
  const words = new Int32Array(p.ex.memory.buffer);
  const at = (i) => words[(base >> 2) + i];
  const items = at(0), hits = at(1);
  let c = 2; const out = [];
  for (let n = 0; n < items; n++) {
    const k = at(c);
    if (k === 0) { out.push(`rect ${at(c+1)} ${at(c+2)} ${at(c+3)} ${at(c+4)} ${rgb(at(c+5))}`); c += 6; }
    else if (k === 1) { out.push(`dot ${at(c+1)} ${at(c+2)} ${at(c+3)} ${rgb(at(c+4))}`); c += 5; }
    else if (k === 2) {
      const len = at(c+5); let s = "";
      for (let i = 0; i < len; i++) s += String.fromCodePoint(at(c+6+i));
      out.push(`text ${at(c+1)} ${at(c+2)} ${at(c+3)} ${rgb(at(c+4))} ${s}`); c += 6 + len;
    } else return post("ERROR unknown record kind " + k);
  }
  for (let n = 0; n < hits; n++) {
    out.push(`hit ${"xy"[at(c+1)]} ${at(c+2)} ${at(c+3)} ${at(c+4)} ${at(c+5)} ${at(c+6)}`);
    c += 7;
  }
  post(out.join("\\n"));
}, 3000);
</script>
"""


def _drawn(site: Path) -> list:
    """What the page's own shell drew, over the wire, from a real
    browser.  The probe is appended to the generated page rather than
    built into it: a gate's affordance is `window.gestatePicture`, and
    the walk belongs to the test."""
    page = site / "index.html"
    page.write_text(page.read_text().replace("</body>", _WIRE_PROBE + "</body>"))
    _Site.result.clear()
    _Site.arrived.clear()
    server, base = _serve(site)
    profile = tempfile.mkdtemp(prefix="gestate-chrome")
    chrome = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--user-data-dir={profile}", f"{base}/index.html"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ok = _Site.arrived.wait(timeout=60)
    finally:
        chrome.kill()
        chrome.wait()
        server.shutdown()
        shutil.rmtree(profile, ignore_errors=True)
    assert ok, "the page never posted its picture — it did not load"
    got = _Site.result[0]
    assert not got.startswith(("ERROR", "REJECT")), got
    return got.strip().split("\n") if got.strip() else []


def _reference(name: str, rate: int = online.RATE) -> list:
    """What `gestate/gui.py` draws from `cx = cy = 0` — the definition of
    correct, and `test_gallery.py` §`_reference` says at length why it
    goes through `Substrate` rather than through a walk assembled beside
    it.  The page places the origin at the canvas centre, so the
    comparison is made against that same centre."""
    from gestate.gui import Substrate, _attachments, _flatten

    canvas = Substrate((AUDIO_DIR / name).read_text(), rate)
    lines = []
    for item in _flatten(canvas.signal.value, canvas.state):
        if item[0] == "rect":
            _, x, y, w, h, (r, g, b) = item
            lines.append(f"rect {x} {y} {w} {h} {r} {g} {b}")
        elif item[0] == "dot":
            _, x, y, rad, (r, g, b) = item
            lines.append(f"dot {x} {y} {rad} {r} {g} {b}")
        else:
            _, x, y, text, (r, g, b), scale = item
            lines.append(f"text {x} {y} {scale} {r} {g} {b} {text}")
    for hit in _attachments(canvas.signal.value, canvas.state):
        x0, y0, x1, y1 = hit["region"]
        lines.append(f"hit {hit['axis']} {hit['chan']} {x0} {y0} {x1} {y1}")
    return lines


def _shift(lines: list, dx: int, dy: int) -> list:
    """The reference, moved to where the page puts the origin."""
    out = []
    for line in lines:
        parts = line.split()
        if parts[0] in ("rect", "dot", "text"):
            parts[1] = str(int(parts[1]) + dx)
            parts[2] = str(int(parts[2]) + dy)
        else:
            for i in (3, 5):
                parts[i] = str(int(parts[i]) + dx)
            for i in (4, 6):
                parts[i] = str(int(parts[i]) + dy)
        out.append(" ".join(parts))
    return out


@needs_tools
@needs_shell
@needs_chrome
@pytest.mark.parametrize("name", DRAWS)
def test_the_page_draws_what_the_desk_draws(name):
    """The row `card:audiovisual-gallery.md` turns on, on the page.

    `test_gallery.py` already holds the *module* to `gui.py` under
    `wasmtime`.  What is between the two and checked nowhere else is the
    **payload this generator writes** — the serialized program, the
    fourteen tags, and the channel names in declaration order.  A tag
    off by one draws a `Row` as whatever shares its number, and a
    chan list in the wrong order gives a fader somebody else's channel;
    both would pass every test in that file and fail on the page.

    So this opens the page a person opens, in a real browser, and reads
    the picture back over the wire.
    """
    with tempfile.TemporaryDirectory() as d:
        site = Path(d) / "site"
        online.generate(AUDIO_DIR / name, site)
        drawn = _drawn(site)
    assert drawn, f"{name} drew nothing"
    assert drawn == _shift(_reference(name), 480 >> 1, 320 >> 1), (
        f"{name}: the page's picture is not the one gui.py draws")


@needs_tools
@needs_shell
def test_a_piece_that_draws_carries_its_substrate_and_its_meters():
    """The generator's half, without a browser.

    **What a piece declares is what it is charged for** — the bargain
    `examples/audio/spectrum.ges` states for the filter bank and `peak`
    makes for the meter.  So the config is a list of what this file
    asked for and never a flag meaning *all of them*.
    """
    with tempfile.TemporaryDirectory() as d:
        site = Path(d) / "site"
        online.generate(AUDIO_DIR / "spectrum.ges", site)
        data = json.loads((site / "spectrum.json").read_text())
        assert (site / online.webshell.NAME).exists()
        assert (site / "canvas.js").exists()
    canvas = data["canvas"]
    assert len(canvas["tags"]) == 14, "the walk decodes cells with all fourteen"
    assert canvas["chans"] == [f"band{k}" for k in range(8)]
    assert canvas["meters"]["bands"] == list(range(8))
    assert canvas["meters"]["peak"] is False, "spectrum declares no peak"
    assert canvas["meters"]["scopes"] == []


@needs_tools
@needs_shell
def test_a_scope_is_carried_as_the_ring_the_module_already_keeps():
    """`scoped.ges`'s trace — the meter that is not a number.

    A `List Float` cannot ride the scalar wire, so the page stages it
    with `web_list` and the worklet reads it from the module's own ring
    through `read_scope_<i>`.  What this holds is that the generator
    names the right reader and the right window, because an index off by
    one reads another scope's ring and would look like a working scope
    drawing the wrong sound.
    """
    src = (AUDIO_DIR / "scoped.ges").read_text()
    from gestate.audiospans import located
    _sites, graph = located(src, rate=online.RATE)
    canvas = online.canvas_of(src, graph)
    assert canvas["meters"]["scopes"] == [
        {"label": "post", "length": 4096, "index": 0,
         "points": online.TRACE_POINTS}]
    #: The label is a channel the canvas declared *and* a scope the graph
    #: keeps — one name doing both jobs is what makes the wiring possible.
    assert "post" in canvas["chans"]
    assert [label for label, _n, _node in graph.scopes()] == ["post"]


def test_the_pages_trace_is_the_editors_trace():
    """One number, in two files, held equal.

    `online.TRACE_POINTS` is repeated rather than imported — the page
    does not otherwise depend on the editor — and a repeated constant is
    two things that can disagree unless something says they may not.
    """
    from gestate.audioeditor import Workbench

    assert online.TRACE_POINTS == Workbench.TRACE_POINTS


@needs_tools
@needs_shell
@needs_chrome
@pytest.mark.parametrize("name,want", [("spectrum.ges", "bands"),
                                       ("substrate.ges", "peak"),
                                       ("scoped.ges", "traces")])
def test_the_instrument_reaches_the_picture(name, want):
    """The meters — *"the meters are cool"*, Henri, 2026-09-04.

    Three of the six pieces draw a picture **of** the sound rather than
    beside it: `spectrum` reads eight bands, `substrate` a `peak`, and
    `scoped` the window its own ring holds.  On the desk those arrive
    once a frame from `gestate/host.c` and the engine's rings; a page has
    no such host, so the worklet measures them next to the samples it is
    already rendering.

    This renders a second through the real worklet in a real browser and
    holds that the report arrived, named what the file declared, and
    **moved** — a bank wired to nothing reports zeros forever, which is
    the failure a presence check would pass.
    """
    with tempfile.TemporaryDirectory() as d:
        site = Path(d) / "site"
        online.generate(AUDIO_DIR / name, site)
        got = _metered(site, FRAMES)
    assert got["reports"] > 0, f"{name}: the worklet never reported"
    last = got["last"]
    assert last is not None and want in last, f"{name}: no {want} in {last}"
    if want == "bands":
        values = list(last["bands"].values())
        assert len(values) == 8
        assert any(v > 0 for v in values), "eight bands and all of them silent"
    elif want == "peak":
        assert last["peak"] > 0, "a piece that makes sound reported no peak"
    else:
        points = last["traces"]["post"]
        assert len(points) == online.TRACE_POINTS
        assert any(p != 0 for p in points), "a trace of a playing signal, flat"


def _metered(site: Path, frames: int) -> dict:
    """The worklet's last meter report, from a real offline render."""
    _Site.result.clear()
    _Site.arrived.clear()
    server, base = _serve(site)
    profile = tempfile.mkdtemp(prefix="gestate-chrome")
    chrome = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--user-data-dir={profile}",
         f"{base}/index.html?check={frames}&meters=1&to=/check"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ok = _Site.arrived.wait(timeout=60)
    finally:
        chrome.kill()
        chrome.wait()
        server.shutdown()
        shutil.rmtree(profile, ignore_errors=True)
    assert ok, "the page never posted its meters"
    return json.loads(_Site.result[0])
