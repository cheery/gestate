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

from gestate import audiowasm, online

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
    under the name it fetches it by."""
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
