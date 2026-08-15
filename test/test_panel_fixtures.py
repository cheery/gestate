"""The plugin's half of the canvas seam — are the fixtures today's export?

`shell/panel/tests/substrate_parity.rs` proves the Rust port draws and
touches what the reference does — against **checked-in copies** of the
export: `substrate.program`/`.tags`/`.display` and the `lantern.*`
family.  Those copies froze the seam at the commit that wrote them, and
until this file nothing compared them with the living exporter: the
serialization could move, the Rust suite would stay green against the
stale bytes, and the first red thing would be somebody's DAW.

That is the failure shape of fixme.md F101 — two artifacts agreeing in
an omission while the wire between them is dead — and *"I saw the
canvas working in the plugin"* was exactly the assumption that hid it.
A seam is only tested while both of its halves are pinned to the same
bytes; this file is the sending half's pin.

So: regenerate every fixture from today's compiler, exporter and
reference walk, and require equality with what the Rust suite reads.
When one of these fails, the export moved.  That is not a defect in
this test — it is the seam saying so.  Regenerate the fixture, run

    cargo test -p gestate-panel --features substrate

and commit the two sides together.

**`--features substrate` is load-bearing, and this line used to omit
it.**  `substrate_parity.rs` opens `#![cfg(feature = "substrate")]` and
the panel's `default = []`, so a plain `cargo test -p gestate-panel`
builds that target, runs *zero* tests out of it, and reports success
without ever reading these bytes.  An instruction that goes green
without checking anything is the same failure this file was written
about, one floor up — so the flag is spelled out rather than assumed.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "shell" / "panel" / "tests"


def _source(name: str) -> str:
    return (ROOT / "examples" / "audio" / name).read_text()


def _knobs_of(source: str, graph) -> frozenset:
    """`export_clap`'s own rule for what becomes a parameter — copied
    from `test_export.py` so the bridge here is derived the same way
    the shipped plugin derives it."""
    from gestate.export import _BEAT_CHANS, bank_channels

    banked = bank_channels(source)
    return frozenset(n.chan for n in graph.control_sources()
                     if n.chan not in banked and n.chan not in _BEAT_CHANS)


def _export(name: str) -> dict:
    from gestate.export import host_graph, substrate_of

    source = _source(name)
    graph = host_graph(source, 48000)
    sub = substrate_of(source, 48000, graph, _knobs_of(source, graph))
    assert sub is not None, f"{name} declares a `substrate`"
    return sub


def _display_lines(name: str) -> list[str]:
    """The reference walk, serialized in the grammar `drawn` parses.

    From `cx = cy = 0`, because that is the reference's own origin —
    the fixture pins the convention, not only the arithmetic (the
    comment above `reference()` in `substrate_parity.rs` says why).

    **And without forcing the channel declarations first.**  A channel's
    id is allocation order, so the same file has two correct readings:
    force the declarations and `cutoff` is 0; let the program reach it
    and `cutoff` is 2 (`export.substrate_of`'s docstring tells this
    story).  The parity suite's `open()` forces `main` alone, so the
    fixture's hit lines carry the second reading, and this walk must
    make the same choice or every `hit` line disagrees about ids while
    all the geometry matches.
    """
    from gestate.gui import _attachments, _entry_signal, _flatten, assembled
    from gestate.pipeline import compile as _compile
    from gestate.reactive import init_program

    state = _compile(assembled(_source(name), 48000))
    init_program(state)
    signal = _entry_signal(state)
    lines = []
    for item in _flatten(signal.value, state):
        kind = item[0]
        if kind == "rect":
            _, x, y, w, h, (r, g, b) = item
            lines.append(f"rect {x} {y} {w} {h} {r} {g} {b}")
        elif kind == "dot":
            _, x, y, rad, (r, g, b) = item
            lines.append(f"dot {x} {y} {rad} {r} {g} {b}")
        elif kind == "text":
            _, x, y, text, (r, g, b), scale = item
            lines.append(f"text {x} {y} {scale} {r} {g} {b} {text}")
        else:
            raise AssertionError(f"unknown item kind {kind!r}")
    for hit in _attachments(signal.value, state):
        x0, y0, x1, y1 = hit["region"]
        lines.append(
            f"hit {hit['axis']} {hit['chan']} {x0} {y0} {x1} {y1}")
    return lines


def _fixture(name: str) -> str:
    path = FIXTURES / name
    assert path.exists(), f"no fixture {path}"
    return path.read_text()


MOVED = ("the export moved: regenerate shell/panel/tests/%s and run "
         "`cargo test -p gestate-panel --features substrate` — the two "
         "sides ship together, and without the flag the Rust half runs "
         "no tests at all")


def test_the_program_fixtures_are_todays_serialization():
    """`crust.serialize`'s text is what the Rust machine boots from."""
    for stem in ("substrate", "lantern"):
        sub = _export(f"{stem}.ges")
        want = _fixture(f"{stem}.program")
        assert sub["text"].rstrip("\n") == want.rstrip("\n"), \
            MOVED % f"{stem}.program"


def test_the_tag_fixtures_are_todays_constructor_table():
    """A tag is a position in this program's own table; the walk decodes
    cells with it, so a stale table draws a `Row` as whatever shares its
    number."""
    for stem in ("substrate", "lantern"):
        sub = _export(f"{stem}.ges")
        want = [int(w) for w in _fixture(f"{stem}.tags").split()]
        assert sub["tags"] == want, MOVED % f"{stem}.tags"


def test_the_display_fixtures_are_todays_reference_walk():
    """What `gui.py` draws is the definition of correct; the fixture is
    that walk written down, and the Rust suite holds the port to it."""
    for stem in ("substrate", "lantern"):
        got = _display_lines(f"{stem}.ges")
        want = [ln for ln in _fixture(f"{stem}.display").splitlines()
                if ln.strip()]
        assert got == want, MOVED % f"{stem}.display"


def test_the_channels_and_bridge_the_rust_suite_carries_are_todays():
    """The other half of this handshake is hardcoded in Rust.

    `substrate_parity.rs` builds its `CanvasProgram`s with literal
    `chans` and `bridge` values — `program()` and `lantern()` — because
    a Rust test cannot ask the exporter.  These literals are that
    fixture, restated from the deriving side: if either assertion moves,
    update both files in one commit or the Rust suite tests a plugin
    the export no longer produces.
    """
    sub = _export("substrate.ges")
    assert sub["chans"] == ["cutoff", "peak"], \
        "substrate_parity.rs program() carries these chans"
    assert sub["bridge"] == [("cutoff", 0)], \
        "substrate_parity.rs program() carries this bridge"

    sub = _export("lantern.ges")
    assert sub["chans"] == ["warmthChan", "glowChan", "peak"], \
        "substrate_parity.rs lantern() carries these chans"
    assert sub["bridge"] == [("warmthChan", 4), ("glowChan", 29)], \
        "substrate_parity.rs lantern() carries this bridge"
