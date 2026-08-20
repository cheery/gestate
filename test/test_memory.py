"""What a session carries across, checked — `doc/memory/README.md` is
the contract.

**This corpus was invisible until 2026-08-20.**  It lived outside the
tree, on one machine, unversioned: 28 files and 2,386 lines, larger than
the five capped method documents put together, and the author had never
read a line of it.  Henri's call that morning was to split it by kind —
the work's memories into the tree, the person's kept private — and this
file is what makes the split hold, on `test_board.py`'s rule that a rule
worth having is executable.

Two failures it exists to catch, both of which are one careless minute:

* **A `user` memory copied in.**  The repository is public, so a note
  about how somebody rests or what he is paid for is published the
  moment it lands here.  `test_consent.py` guards other people's names;
  this guards the author's own.
* **A memory nobody can find.**  Recall reads the index, and a body with
  no index line is a fact that will never be recalled — worse than not
  written, because it looks written.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MEMORY = ROOT / "doc" / "memory"
INDEX = MEMORY / "README.md"

#: The kinds that may stand in a public tree.  `user` is deliberately
#: absent — see the docstring, and `doc/memory/README.md` §"The split".
PUBLIC = ("project", "feedback", "reference")

#: `- [Title](name.md) — hook`, the one-line index entry.
ENTRY = re.compile(r"^- \[[^\]]+\]\(([^)]+\.md)\)")


def memories() -> list[Path]:
    return sorted(p for p in MEMORY.glob("*.md") if p.name != "README.md")


def front(path: Path) -> dict[str, str]:
    """The frontmatter, flattened — `metadata.type` arrives as `type`."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        found = re.match(r"^\s*(\w+):\s*(.*)$", line)
        if found and found.group(2).strip():
            out[found.group(1)] = found.group(2).strip().strip('"')
    return out


def indexed() -> list[str]:
    return [m.group(1) for m in
            (ENTRY.match(line) for line in INDEX.read_text(encoding="utf-8").splitlines())
            if m]


def test_the_directory_is_there_with_its_contract():
    assert INDEX.exists(), (
        "doc/memory/README.md is the contract for this directory and it "
        "is gone.  A memory corpus with no stated split is how a private "
        "note about the author reaches a public tree.")
    assert memories(), "doc/memory/ holds no memories, which is not a state anybody chose."


@pytest.mark.parametrize("path", memories(), ids=lambda p: p.name)
def test_every_memory_names_itself(path: Path):
    fields = front(path)
    assert fields, (
        f"{path.name} opens with no `---` frontmatter.  Recall reads "
        f"`description`; a memory without one is never recalled.")
    assert fields.get("name") == path.stem, (
        f"{path.name} says `name: {fields.get('name')}`.  The filename is "
        f"the id — it is what `[[{path.stem}]]` resolves to — so the two "
        f"cannot disagree.")
    assert fields.get("description"), (
        f"{path.name} has no `description`.  That line is what decides "
        f"whether this memory is ever looked at again.")


@pytest.mark.parametrize("path", memories(), ids=lambda p: p.name)
def test_no_memory_about_the_person_is_published(path: Path):
    kind = front(path).get("type")
    assert kind in PUBLIC, (
        f"{path.name} is `type: {kind}`, which does not belong in a public "
        f"tree.  doc/memory/README.md §\"The split\": the work's memories "
        f"live here, the person's stay in the private directory.  If this "
        f"is genuinely about the work, say so in its type.")


def test_every_memory_is_in_the_index():
    listed, present = set(indexed()), {p.name for p in memories()}
    missing = sorted(present - listed)
    assert not missing, (
        f"not in doc/memory/README.md's index: {', '.join(missing)}.  "
        f"A body with no index line is a fact that will never be "
        f"recalled — add a `- [Title](file.md) — hook` line.")


def test_the_index_points_at_files_that_exist():
    stale = sorted(name for name in indexed() if not (MEMORY / name).exists())
    assert not stale, (
        f"doc/memory/README.md indexes files that are gone: "
        f"{', '.join(stale)}.  A memory is deleted when it turns out to "
        f"be wrong, and the index line goes with it.")


def test_the_index_lists_each_memory_once():
    seen = indexed()
    twice = sorted({name for name in seen if seen.count(name) > 1})
    assert not twice, (
        f"indexed twice in doc/memory/README.md: {', '.join(twice)}.  "
        f"Two hooks for one fact is two things that can drift apart.")
