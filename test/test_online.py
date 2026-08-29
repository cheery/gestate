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

Skips, naming the tool, without `clang`/`wasm-ld` or a Chrome.
"""

from __future__ import annotations

import http.server
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


def _rendered(site: Path, frames: int) -> list:
    """Open the page's check mode in a headless Chrome and wait for the
    frames it POSTs back.  Wall clock, not `--virtual-time-budget`: an
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
         f"{base}/index.html?check={frames}&to=/check"],
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
@pytest.mark.parametrize("name", ["twinkle.ges", "twoknobs.ges", "gyre.ges"])
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
def test_an_unfolding_score_is_refused_with_the_reason():
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(online.OnlineError, match="unfolds"):
            online.generate(AUDIO_DIR / "arpeggiator.ges", d)
