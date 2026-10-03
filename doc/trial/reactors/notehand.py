"""The note hand's measure — expectation 14, `doc/memory/expectations-dug-up.md`.

    python doc/trial/reactors/notehand.py

`card:gui-is-difficult.md` §"Built — the notes editor's note hand".  The
claim: the ported part under a tenth of what it replaces.  The rule is
the expectation's own — a line counts when it is not blank and not a
comment, docstrings included.

**What it replaces** is the note hand of today: `gestate/hand.ges` and
eleven methods of `gestate/session.py`.  **What the port does not
cover** is subtracted, each span named below by the text it starts and
ends at, so the judgment is on the page and can be argued with: the
note's end (grow, resize), the band (sweep, select, clear), the group,
the audition, the interval said while dragging, the transcript, the
ruler sharing the hand, a press declined by a box of a page, the probe's
agreement bookkeeping, and the bar last pressed.  Where a span is in
doubt it is subtracted, which is the direction that works against the
claim.

**What the port is** is `examples/gui/carry.ges` less its document's
declaration (the relation, `model`, `lines`, the `document` line) and
the silent `sound`, which a document-reading program owes whatever its
GUI — both printed, so the other reading is one subtraction away.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

METHODS = ["_note_touched", "_hit", "_hand_event", "_hand_act", "_snapped",
           "_carried", "_interval", "_written_at", "_commit_move",
           "_show_moved", "released"]

#: `(method, first line's text, last line's text)` — uncovered, inclusive.
UNCOVERED = [
    ("_note_touched", "self._journal().slid", "self._journal().slid"),
    ("_note_touched", 'if getattr(found, "on_note"', 'return ""'),
    ("_note_touched", 'if getattr(found, "on_ruler"', "return self._ruler_touched"),
    ("_note_touched", "if self.sizing is not None", "# the ruler has the hand"),
    ("_note_touched", "if found.box in self.declined", "# a press that was never"),
    ("_note_touched", "if not owns(roll, down)", '("Abort",))'),
    ("_note_touched", "self._bar_pressed(roll, tick_at", "self._bar_pressed(roll, tick_at"),
    ("_hit", "named = self.named_note.pop", "named = self.named_note.pop"),
    ("_hit", "across = self.rail_at.get", "self.disagreed.append"),
    ("_hit", "at = x_of(roll, tick)", 'return ("OnEnd", max('),
    ("_hit", "on, off = roll.events[note][:2]", 'return ("OnEnd", note) if edge'),
    ("_hand_act", 'if head not in ("Grab"', "self._hush(found)"),
    ("_hand_act", "self.selected[box] = note", "self._hold(found)"),
    ("_hand_act", "self._sound(found, note, roll.events", "return self._written_at"),
    ("_hand_act", "self._sound(found, note, key)", "return self._interval"),
    ("_hand_act", 'if head == "Grow"', "return f\"hand.ges asked for"),
    ("_interval", "def _interval", "return"),
    ("_written_at", "def _written_at", "of {where[0]}{tail}"),
    ("_commit_move", "if dt:", "self._bar_pressed(roll, at)"),
    ("_commit_move", "group = self.group.get", "group = self.group.get"),
    ("released", "sz = self.sizing", "return self._ruler_event(regions[sz[0]]"),
    ("released", 'self._journal().add("released", (name,), "")', 'self._journal().add("released", (name,), "")'),
    ("released", "if found.box in self.declined", 'return ""'),
    ("released", 'doing = getattr(self.bench, "released"', 'return said or ""'),
]

#: `hand.ges` lines that belong to the end, the band, or an abort.
HAND_UNCOVERED = re.compile(
    r"\b(Ending|Ended|Sweeping|Swept|GrabEnd|Grow|Resize|Sweep|Select|Clear|Drop|Abort|OnEnd|OnRoll)\b")


def code(line: str) -> bool:
    s = line.strip()
    return bool(s) and not s.startswith("#") and not s.startswith("//")


def methods() -> dict[str, list[str]]:
    src = (ROOT / "gestate" / "session.py").read_text()
    lines = src.split("\n")
    out = {}
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name in METHODS and node.name not in out:
            if node.name == "released" and "def released(self, name: str)" not in lines[node.lineno - 1]:
                continue
            out[node.name] = lines[node.lineno - 1:node.end_lineno]
    return out


def uncovered_in(name: str, body: list[str]) -> int:
    n, taken = 0, set()
    for method, first, last in UNCOVERED:
        if method != name:
            continue
        start = next((i for i, l in enumerate(body) if first in l and i not in taken), None)
        if start is None:
            raise SystemExit(f"{name}: no line says {first!r} — the span moved; re-read it")
        end = next((i for i in range(start, len(body)) if last in body[i]), None)
        if end is None:
            raise SystemExit(f"{name}: nothing after {first!r} says {last!r}")
        for i in range(start, end + 1):
            if i not in taken and code(body[i]):
                n += 1
            taken.add(i)
    return n


def main() -> None:
    whole = cut = 0
    for name, body in methods().items():
        lines = sum(code(l) for l in body)
        gone = uncovered_in(name, body)
        whole += lines
        cut += gone
        print(f"  session.{name:14} {lines:4}  uncovered {gone:3}")
    hand = (ROOT / "gestate" / "hand.ges").read_text().split("\n")
    h_all = sum(code(l) for l in hand)
    h_cut = sum(code(l) and bool(HAND_UNCOVERED.search(l)) for l in hand)
    print(f"  hand.ges               {h_all:4}  uncovered {h_cut:3}")
    replaced_all, replaced = whole + h_all, whole + h_all - cut - h_cut

    port = (ROOT / "examples" / "gui" / "carry.ges").read_text().split("\n")
    heads = ("include", "levels", "noteRel", "model", "lines", "type", "tune", "sound")
    owed, cur = 0, None
    for l in port:
        if not code(l):
            continue
        if not l.startswith(" "):
            cur = l.split()[0]
        if cur in heads:
            owed += 1
    total = sum(code(l) for l in port)
    hand_port = total - owed
    print(f"\nreplaced: {replaced_all} today, {replaced} of it covered by the port")
    print(f"port: {total} lines, {owed} of them the document's declaration and the silence"
          f" — the hand is {hand_port}")
    print(f"ratio: {hand_port / replaced:.2f} of what it covers"
          f" ({total / replaced:.2f} counting the declaration); the claim is under 0.10")


if __name__ == "__main__":
    main()
