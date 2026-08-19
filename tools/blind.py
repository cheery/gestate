"""The judging sheet for a blind multi-arm run — facts first, prose last.

    python tools/blind.py --batch 2 ../arm-1 ../arm-2 ../arm-3

**Why this exists.**  On 2026-08-19 three cold agents worked batch 1 of
`card:ungated-fixes.md` and Henri judged the fifteen verdicts blind.  It
was hard, and he said so: *"this judgement was hard for me.  next time,
if we repeat this test, I'd like more visual indication and some aid in
judgement."*

The fault was the sheet, not the question.  It rendered each arm's raw
markdown, so **one line versus paragraphs was the loudest thing on the
page and accuracy was invisible** — checking accuracy needed five test
bodies read.  He judged what was visible.  Form and accuracy came apart:
the arm he would have committed had a wrong verdict on F153.

**The insight that shapes this file: most of "is this verdict right?" is
machine-checkable.**  An arm names a gate.  Whether that file exists,
whether it contains the name that was cited, and whether it mentions the
F-number are *facts*, and asking a person to establish them by eye
across three arms is the work that made judging hard.  It is also not
judgement at all.  So this computes them, and what is left for the
reader is the part that is genuinely theirs — where the checks pass and
the *reasoning* differs, which is exactly where a difference between
models would show.

**What it must never do**, and each has a reason paid for:

* **Name the models, or show wall-clock and token cost.**  All three
  leak the arm.  The sheet carries A, B, C in a shuffled order and the
  mapping is printed to the terminal for the experimenter, never
  written into the page.
* **Mark which arm the experimenter thinks is right.**  That destroys
  the independent read the review exists to provide — Henri's own rule:
  *"it's better that I reflect on them.  Just like it's with humans.
  Nobody does good decisions alone."*
* **Let length carry meaning.**  The verdict shows as one line; the
  arm's prose sits behind a disclosure.  `board/README.md` already says
  paragraphs belong to the journal, so an arm that wrote one is a form
  question and not an accuracy question, and the two must not be
  confused again.
"""

from __future__ import annotations

import argparse
import html
import random
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEETS = ROOT / "test" / "blind"

#: `### F169. **[fixed]** the wrist clock understated …`
ENTRY = re.compile(r"^### F(\d+)\.\s*(.*)$", re.M)
#: The verdict line an arm adds, and its continuation to the first blank.
GATE = re.compile(r"^gate:(.*?)(?=\n\s*\n|\Z)", re.M | re.S)
#: Anything in backticks that looks like a path or a `path::name`.
CITE = re.compile(r"`([^`\n]+)`")
PATHISH = re.compile(r"^[\w./-]+\.(py|rs|c|h|ges|samples|md)(::[\w:.-]+)?$")


def _rel(path: Path) -> Path:
    """`path` under the tree, or the path itself.

    Same guard and same reason as `tools/driven.py::_rel`: this is
    called *after* the sheet has been written, and losing the finished
    page to a `relative_to` raise would be an absurd way to end a run
    that cost three agents.
    """
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def entries(fixme: Path) -> dict[str, str]:
    """Every entry's body, by F-number, from one arm's `fixme.md`.

    **An arm with no file is a result, not a crash.**  A run that died,
    or was killed, or never wrote anything is one of the things this
    comparison exists to notice; a traceback here would lose the other
    two arms' work along with it.  The entry then reads `missing` on the
    sheet, which is what happened.
    """
    if not fixme.is_file():
        return {}
    text = fixme.read_text(encoding="utf-8")
    found, marks = {}, list(ENTRY.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        found[f"F{m.group(1)}"] = text[m.start():end]
    return found


def verdict_of(body: str) -> tuple[str, str, list[str]]:
    """`(kind, one_line, citations)` for an entry, or `("missing", …)`.

    **`kind` is deliberately coarse** — `gated`, one of the `none`
    flavours, or `missing`.  Two arms that both said *nothing can* agree
    at the level a reader cares about even if the sentences differ, and
    an agreement measure that counted prose would report every entry as
    split.
    """
    m = GATE.search(body)
    if not m:
        return "missing", "— no gate: line —", []
    said = " ".join(m.group(1).split())
    cites = [c for c in CITE.findall(said) if PATHISH.match(c)]
    low = said.lower()
    if re.search(r"\bnone\b", low) and not cites:
        for flavour in ("not a repair", "nothing can", "not yet built"):
            if flavour in low:
                return f"none — {flavour}", said, []
        return "none — other", said, []
    return "gated", said, cites


# ── the mechanical checks: facts, never opinions ─────────────────────────
#
# Each returns a plain verdict a reader can re-run themselves.  Nothing
# here says whether the citation is *the right* gate — only whether it is
# a thing that exists and says what the arm claimed.  That line is the
# whole discipline of this file: the moment a check starts expressing a
# preference it is biasing the read it exists to serve.


def collected_by_pytest(rel: str) -> bool:
    return rel.startswith("test/") and Path(rel).name.startswith("test_")


def kind_of(rel: str) -> str:
    if rel.endswith(".samples"):
        return "golden sample"
    if rel.endswith(".rs"):
        return "rust test" if "/tests/" in rel or "test" in Path(rel).stem else "rust source"
    if rel.endswith(".ges"):
        return "example / transcript"
    if collected_by_pytest(rel):
        return "pytest"
    return "other"


def check(cite: str, fnum: str, tree: Path) -> dict:
    """Does this citation exist, name what was cited, and know the F-number?"""
    rel, _, member = cite.partition("::")
    path = tree / rel
    out = {"cite": cite, "kind": kind_of(rel), "exists": path.is_file(),
           "member": None, "mentions": None, "collected": False}
    if not out["exists"]:
        # **Nothing further is said about a file that is not there.**
        # The first version reported `pytest · collected` for a cited
        # path that did not exist — a true statement about the *shape*
        # of the name, printed as a fact about a file, on a sheet whose
        # whole job is to separate facts from impressions.
        return out
    out["collected"] = collected_by_pytest(rel)
    text = path.read_text(encoding="utf-8", errors="replace")
    if member:
        out["member"] = bool(re.search(rf"\b{re.escape(member)}\b", text))
    out["mentions"] = fnum in text
    return out


def batch_of(card: Path, n: int) -> list[str]:
    """Row `n` of the card's own schedule table, so the batch is never
    re-typed into a second place."""
    for line in card.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] == str(n):
            return cells[2].split()
    raise SystemExit(f"blind: the card's schedule has no batch {n}")


# ── the sheet ────────────────────────────────────────────────────────────

#: **The sheet is an andon board**, which is this project's own word for
#: it: a lamp that says where a person is needed, and quiet everywhere
#: else.  The palette is taken from the editor's own screen rather than
#: invented — its comment amber is the lamp, its type teal is agreement —
#: so the instrument looks like the thing it is judging.
CSS = """
:root{
  --bg:#f4f4f1; --card:#fffefc; --ink:#1b1f27; --dim:#6a7180; --line:#dcdcd6;
  --lamp:#b8791f; --lamp-wash:#f7ecd9; --agreed:#2c7261; --fail:#a3372c;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#14181f; --card:#1b2029; --ink:#dfe3ea; --dim:#8d95a3; --line:#2c333f;
  --lamp:#e0a94a; --lamp-wash:#2a2419; --agreed:#5fb3a1; --fail:#f08a80;
}}
:root[data-theme="dark"]{
  --bg:#14181f; --card:#1b2029; --ink:#dfe3ea; --dim:#8d95a3; --line:#2c333f;
  --lamp:#e0a94a; --lamp-wash:#2a2419; --agreed:#5fb3a1; --fail:#f08a80;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:400 15px/1.6 "IBM Plex Sans",ui-sans-serif,system-ui,sans-serif;
  padding:2.5rem 1.25rem 6rem}
main{max-width:62rem;margin:0 auto;display:flex;flex-direction:column;gap:2.25rem}
h1{font-size:1.6rem;font-weight:600;letter-spacing:-.01em;margin:0;
   text-wrap:balance}
.lede{color:var(--dim);margin:.5rem 0 0;max-width:44rem;font-size:.94rem}
.strip{display:flex;gap:0;border:1px solid var(--line);border-radius:8px;
  overflow:hidden;background:var(--card)}
.cell{flex:1;padding:.85rem 1rem;border-right:1px solid var(--line)}
.cell:last-child{border-right:0}
.cell b{display:block;font:600 1.5rem/1.1 "IBM Plex Mono",ui-monospace,monospace;
  font-variant-numeric:tabular-nums}
.cell span{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;
  color:var(--dim)}
.cell.lit b{color:var(--lamp)} .cell.calm b{color:var(--agreed)}
section>h2{font:600 .78rem/1 "IBM Plex Sans",sans-serif;letter-spacing:.12em;
  text-transform:uppercase;color:var(--dim);margin:0 0 .25rem}
section>p.note{color:var(--dim);font-size:.88rem;margin:0 0 1.1rem;max-width:44rem}
.stack{display:flex;flex-direction:column;gap:.9rem}
.entry{background:var(--card);border:1px solid var(--line);border-radius:8px;
  border-left:3px solid var(--agreed);padding:.95rem 1.1rem;overflow-x:auto}
.entry.split{border-left-color:var(--lamp);background:
  linear-gradient(90deg,var(--lamp-wash),var(--card) 22rem)}
.hd{display:flex;gap:.7rem;align-items:baseline;flex-wrap:wrap;margin-bottom:.75rem}
.f{font:600 1rem/1 "IBM Plex Mono",ui-monospace,monospace}
.ttl{color:var(--dim);font-size:.88rem}
.tag{margin-left:auto;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--dim)}
.entry.split .tag{color:var(--lamp);font-weight:600}
table{border-collapse:collapse;width:100%;font-size:.86rem}
th{font:600 .68rem/1 "IBM Plex Sans",sans-serif;letter-spacing:.09em;
  text-transform:uppercase;color:var(--dim);text-align:left;
  padding:0 .55rem .4rem;border-bottom:1px solid var(--line)}
td{padding:.4rem .55rem;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:0}
.arm{font:600 .9rem/1 "IBM Plex Mono",monospace;width:1.6rem;color:var(--dim)}
code{font:400 12.5px/1.45 "IBM Plex Mono",ui-monospace,monospace;
  background:color-mix(in srgb,var(--ink) 6%,transparent);
  padding:.12rem .35rem;border-radius:3px;white-space:nowrap}
.chk{text-align:center;font-family:"IBM Plex Mono",monospace;
  font-variant-numeric:tabular-nums;width:4.5rem}
.ok{color:var(--agreed)} .no{color:var(--fail)} .un{color:var(--dim);opacity:.55}
.kind{color:var(--dim);font-size:.78rem;white-space:nowrap}
details{margin-top:.8rem;border-top:1px solid var(--line);padding-top:.6rem}
summary{cursor:pointer;color:var(--dim);font-size:.8rem;list-style:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"▸ ";color:var(--lamp)}
details[open] summary::before{content:"▾ "}
summary:focus-visible{outline:2px solid var(--lamp);outline-offset:2px}
details pre{white-space:pre-wrap;font:400 12.5px/1.55 "IBM Plex Mono",monospace;
  color:var(--dim);margin:.5rem 0 0}
.empty{color:var(--dim);font-size:.88rem;font-style:italic}
"""


def mark(v):
    """A check's answer, and **`·` when there is nothing to say** — a
    missing file has no member and mentions nothing, and printing a
    cross there would read as a second failure rather than as silence."""
    return ('<span class="ok">\u2713</span>' if v is True else
            '<span class="no">\u2717</span>' if v is False else
            '<span class="un">\u00b7</span>')


def render(rows, batch, n) -> str:
    e = html.escape
    unan = [r for r in rows if r["agree"]]
    split = [r for r in rows if not r["agree"]]

    def block(r):
        cls = "entry" if r["agree"] else "entry split"
        tag = "agreed" if r["agree"] else "needs you"
        out = [f'<div class="{cls}"><div class="hd">'
               f'<span class="f">{e(r["f"])}</span>'
               f'<span class="ttl">{e(r["title"])}</span>'
               f'<span class="tag">{tag}</span></div>',
               "<table><thead><tr><th></th><th>verdict</th><th>cites</th>"
               '<th class="chk">exists</th><th class="chk">names it</th>'
               f'<th class="chk">knows {e(r["f"])}</th><th>kind</th>'
               "</tr></thead><tbody>"]
        for arm in "ABC":
            a = r["arms"][arm]
            if not a["checks"]:
                out.append(f'<tr><td class="arm">{arm}</td>'
                           f'<td><code>{e(a["kind"])}</code></td>'
                           f'<td colspan="4" class="kind">nothing cited to check</td>'
                           f'<td class="kind">\u2014</td></tr>')
                continue
            for j, c in enumerate(a["checks"]):
                out.append(
                    f'<tr><td class="arm">{arm if j == 0 else ""}</td>'
                    f'<td>{"<code>" + e(a["kind"]) + "</code>" if j == 0 else ""}</td>'
                    f'<td><code>{e(c["cite"])}</code></td>'
                    f'<td class="chk">{mark(c["exists"])}</td>'
                    f'<td class="chk">{mark(c["member"])}</td>'
                    f'<td class="chk">{mark(c["mentions"])}</td>'
                    f'<td class="kind">{e(c["kind"])}'
                    f'{" \u00b7 collected" if c["collected"] else ""}</td></tr>')
        out.append("</tbody></table>")
        for arm in "ABC":
            out.append(f'<details><summary>{arm} \u2014 what it wrote</summary>'
                       f'<pre>{e(r["arms"][arm]["said"])}</pre></details>')
        return "".join(out) + "</div>"

    return f"""<title>Batch {n} andon</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?\
family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>{CSS}</style>
<main>
<header>
  <h1>Batch {n} &mdash; three arms, blind</h1>
  <p class="lede">Each arm worked the same {len(batch)} entries and wrote one
  <code>gate:</code> line. They are <b>A</b>, <b>B</b>, <b>C</b> in a shuffled
  order and the mapping is not on this page. Nothing here says which arm is
  right &mdash; the marks are facts you can re-run: does the cited file exist,
  does it contain the name that was cited, does it mention the F&#8209;number.</p>
</header>

<div class="strip">
  <div class="cell lit"><b>{len(split)}</b><span>need you</span></div>
  <div class="cell calm"><b>{len(unan)}</b><span>agreed</span></div>
  <div class="cell"><b>{len(rows)}</b><span>entries</span></div>
  <div class="cell"><b>3</b><span>arms</span></div>
</div>

<section>
  <h2>Needs you</h2>
  <p class="note">The arms disagree about the verdict or about which instrument
  holds it. This is the judgement, and it is the whole of it.</p>
  <div class="stack">{''.join(block(r) for r in split)
    or '<p class="empty">None &mdash; all three agreed everywhere.</p>'}</div>
</section>

<section>
  <h2>Agreed</h2>
  <p class="note">All three said the same thing. Worth a glance rather than a
  decision &mdash; three arms can agree and all be wrong, and the marks are the
  cheap way to see that.</p>
  <div class="stack">{''.join(block(r) for r in unan)
    or '<p class="empty">None.</p>'}</div>
</section>
</main>"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python tools/blind.py")
    ap.add_argument("--batch", type=int, required=True)
    ap.add_argument("arms", nargs=3, help="the three arms' checkouts")
    ap.add_argument("--tree", default=str(ROOT),
                    help="the tree the citations are checked against")
    args = ap.parse_args(argv)

    card = ROOT / "board" / "ungated-fixes.md"
    if not card.exists():
        card = ROOT / "board" / "done" / "ungated-fixes.md"
    batch = batch_of(card, args.batch)
    tree = Path(args.tree).resolve()

    # **Shuffled here, and the mapping never reaches the page.**  Wall
    # clock and token cost are not collected at all: both leak the arm,
    # and a number that must not be shown is safest never gathered.
    paths = [Path(a).resolve() for a in args.arms]
    order = paths[:]
    random.shuffle(order)
    named = dict(zip("ABC", order))

    rows = []
    titles = entries(tree / "fixme.md")
    for f in batch:
        title = ""
        if f in titles:
            title = " ".join(titles[f].splitlines()[0].split()[2:])[:70]
        arms, kinds = {}, set()
        for arm, path in named.items():
            kind, said, cites = verdict_of(entries(path / "fixme.md").get(f, ""))
            arms[arm] = {"kind": kind, "said": said, "cites": cites,
                         "checks": [check(c, f, tree) for c in cites]}
            kinds.add((kind, tuple(sorted(cites))))
        rows.append({"f": f, "title": re.sub(r"\*+", "", title),
                     "arms": arms, "agree": len(kinds) == 1})

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = SHEETS / f"{stamp}-batch{args.batch}"
    out.mkdir(parents=True, exist_ok=True)
    sheet = out / "sheet.html"
    sheet.write_text(render(rows, batch, args.batch), encoding="utf-8")

    # To the terminal, for the experimenter, and nowhere else.
    print(f"blind: {_rel(sheet)}")
    print(f"blind: {sum(r['agree'] for r in rows)} of {len(rows)} unanimous")
    print("\nthe mapping — do NOT paste this to the judge:")
    for arm, path in named.items():
        print(f"  {arm} = {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
