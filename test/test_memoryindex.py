"""`tools/memoryindex.py` — the boot surface's invisible half, generated.

Measured 2026-08-24: 19 of 53 memories in the tree were hooked by
nothing in the private index every session reads first.  The index is
outside the repository, so the tree cannot hold it — it can only hold
the source its public half is generated from, and check the generation.
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import memoryindex  # noqa: E402

import pytest  # noqa: E402

README = """# doc/memory/

prose

## The index

- [One](one.md) — the first hook
- [Two](two.md) — **bold** and `code`
"""


def test_every_hook_in_the_readme_is_in_the_block(tmp_path):
    (tmp_path / "README.md").write_text(README)
    b = memoryindex.block(tmp_path / "README.md", root=pathlib.Path("/r"))
    assert "- [One](/r/doc/memory/one.md) — the first hook" in b
    assert "- [Two](/r/doc/memory/two.md) — **bold** and `code`" in b
    assert b.startswith(memoryindex.OPEN) and b.endswith(memoryindex.CLOSE)


def test_the_private_section_is_never_touched(tmp_path):
    (tmp_path / "README.md").write_text(README)
    new = memoryindex.block(tmp_path / "README.md", root=pathlib.Path("/r"))
    index = ("# Memory index\n\npreamble\n\n## In the tree — doc/memory/\n\n"
             "- [Stale](/r/doc/memory/stale.md) — by hand\n\n"
             "## Private — about the person\n\n- [Secret](secret.md) — his\n")
    out = memoryindex.apply(index, new)
    assert "- [Secret](secret.md) — his" in out
    assert "preamble" in out
    assert "stale.md" not in out, "the first run replaces the hand-written hooks"
    assert out.count(memoryindex.OPEN) == 1
    # a second run is idempotent and a hand edit inside the block is undone
    edited = out.replace(memoryindex.CLOSE, "- [Hand](x.md) — smuggled\n" + memoryindex.CLOSE)
    assert memoryindex.apply(edited, new) == out


def test_the_real_readme_yields_every_memory():
    names = {name for _, name, _ in memoryindex.hooks()}
    files = {p.name for p in (ROOT / "doc" / "memory").glob("*.md")} - {"README.md"}
    assert names == files


def test_this_machines_index_is_in_step():
    """The check, where it can see.  Skips where the index is not —
    another machine, a seed, and **this tree's own fence**, which binds
    only the repository: `tools/suite.py` runs fenced, so at a commit
    this skips and `tools/pre-commit.sh` runs
    `tools/memoryindex.py --check` itself, unfenced, after the gates.
    The skip says so because a skip that looks like a pass is the
    failure `test/gates.md` exists to name."""
    path = memoryindex.DEFAULT
    if not path.is_file():
        pytest.skip(f"no private index at {path} — nothing to hold in step here")
    old = path.read_text(encoding="utf-8")
    assert memoryindex.apply(old, memoryindex.block()) == old, (
        "the private index is behind doc/memory/README.md — run: python tools/memoryindex.py")
