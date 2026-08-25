#!/usr/bin/env python3
#: asked-by: a session, 2026-08-24 — built because the deck needed
#: presenting (commit b6110dc, "for the future keepers"); the deck
#: itself is Henri's, doc/teaching/keepers-first-week.md
"""slides.py — render a slide-deck markdown file into one self-contained HTML page.

    python3 tools/slides.py doc/teaching/keepers-first-week.md

The source format is the one doc/teaching/ uses: each `## N. Title`
heading is a slide; the lines under it are what is on screen; a
paragraph beginning `**Speak:**` is the presenter's notes.  Sections
whose headings are not numbered (the header block, "Changed in…",
"What review should judge") are not slides and are left out.

Controls in the browser: arrows/space/PgUp/PgDn to move, Home/End to
jump, `n` toggles the speaker notes.  Built 2026-08-24 because the
keeper teaching deck needed presenting; nothing else uses it yet.
"""
import html
import re
import subprocess
import sys
from pathlib import Path


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+(?:\*[^*]+)*?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', s)
    return s


def block_html(block):
    lines = block.splitlines()
    if all(l.lstrip().startswith('|') for l in lines) and len(lines) >= 2:
        rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in lines]
        rows = [r for r in rows if not all(set(c) <= set('-: ') for c in r)]
        head, body = rows[0], rows[1:]
        out = ['<table>', '<thead><tr>']
        out += [f'<th>{inline(c)}</th>' for c in head]
        out.append('</tr></thead><tbody>')
        for r in body:
            out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>')
        out.append('</tbody></table>')
        return ''.join(out)
    if all(re.match(r'\s*\* ', l) for l in lines):
        items = re.split(r'^\s*\* ', block, flags=re.M)[1:]
        return '<ul>' + ''.join(f'<li>{inline(" ".join(i.split()))}</li>' for i in items) + '</ul>'
    text = inline(' '.join(' '.join(lines).split()))
    if text.startswith('—'):
        return f'<p class="attrib">{text}</p>'
    return f'<p>{text}</p>'


def parse(src):
    slides = []
    for m in re.finditer(r'^## (\d+)\. (.*?)$\n(.*?)(?=^## |\Z)', src, re.M | re.S):
        num, title, body = m.group(1), m.group(2), m.group(3)
        body = body.strip().split('\n---')[0]
        blocks = [b for b in re.split(r'\n\s*\n', body) if b.strip()]
        screen, notes = [], []
        for b in blocks:
            (notes if b.lstrip().startswith('**Speak:**') else screen).append(b)
        slides.append({
            'num': num, 'title': inline(title),
            'screen': ''.join(block_html(b) for b in screen),
            'notes': ''.join(block_html(re.sub(r'^\s*\*\*Speak:\*\*\s*', '', b)) for b in notes),
        })
    return slides


CSS = """
:root { --bg:#14161a; --fg:#e8e6e0; --dim:#9a968c; --acc:#d8b56a; }
* { margin:0; padding:0; box-sizing:border-box; }
html,body { height:100%; background:var(--bg); color:var(--fg);
  font:400 100%/1.45 system-ui, "Segoe UI", sans-serif; }
.slide { display:none; height:100vh; padding:6vh 9vw; flex-direction:column;
  justify-content:center; overflow:auto; }
.slide.on { display:flex; }
h1 { font-size:3.2rem; line-height:1.15; margin-bottom:5vh; font-weight:650; }
h1 .no { color:var(--acc); margin-right:.6em; font-weight:400; }
.screen p { font-size:1.9rem; margin:2.2vh 0; max-width:34em; }
.screen p.attrib { font-size:1.3rem; color:var(--dim); }
.screen ul { margin:2.2vh 0 2.2vh 1.4em; }
.screen li { font-size:1.7rem; margin:1.2vh 0; max-width:30em; }
.screen strong { color:var(--acc); }
.screen em { color:var(--fg); }
.screen code { font-family:ui-monospace,monospace; font-size:.85em;
  background:#22252b; padding:.1em .3em; border-radius:.2em; }
.screen table { border-collapse:collapse; font-size:1.4rem; margin:2.5vh 0; }
.screen th,.screen td { border-bottom:1px solid #333842; padding:.45em 1.1em .45em 0; text-align:left; }
.screen th { color:var(--dim); font-weight:500; }
.notes { display:none; border-top:1px solid #333842; margin-top:4vh; padding-top:2.5vh; }
body.shownotes .notes { display:block; }
.notes p { color:var(--dim); font-size:1.15rem; max-width:52em; margin:.8vh 0; }
.notes strong { color:var(--fg); }
#hud { position:fixed; right:1.2rem; bottom:.9rem; color:var(--dim);
  font-size:.85rem; user-select:none; }
"""

JS = """
var i = 0, S = document.querySelectorAll('.slide');
function show(n) {
  i = Math.max(0, Math.min(S.length - 1, n));
  S.forEach(function(s, k){ s.classList.toggle('on', k === i); });
  document.getElementById('hud').textContent = (i + 1) + ' / ' + S.length;
  history.replaceState(null, '', '#' + (i + 1));
}
addEventListener('keydown', function(e) {
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') show(i + 1);
  else if (e.key === 'ArrowLeft' || e.key === 'PageUp') show(i - 1);
  else if (e.key === 'Home') show((parseInt(location.hash.slice(1), 10) || 1) - 1);
  else if (e.key === 'End') show(S.length - 1);
  else if (e.key === 'n') document.body.classList.toggle('shownotes');
  else return;
  e.preventDefault();
});
show((parseInt(location.hash.slice(1), 10) || 1) - 1);
"""


def main():
    src_path = Path(sys.argv[1])
    src = src_path.read_text()
    slides = parse(src)
    if not slides:
        sys.exit(f'slides.py: no numbered "## N. Title" slides in {src_path}')
    try:
        commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                                capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = 'unknown'
    title = re.sub(r'<[^>]+>', '', slides[0]['title'])
    body = []
    for s in slides:
        body.append(f'<section class="slide"><h1><span class="no">{s["num"]}</span>{s["title"]}</h1>'
                    f'<div class="screen">{s["screen"]}</div>'
                    f'<div class="notes">{s["notes"]}</div></section>')
    out = (f'<!doctype html>\n<!-- generated by tools/slides.py from {src_path} at {commit};'
           f' edit the .md and regenerate -->\n'
           f'<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
           f'<style>{CSS}</style></head><body>\n' + '\n'.join(body) +
           f'\n<div id="hud"></div><script>{JS}</script></body></html>\n')
    out_path = src_path.with_suffix('.html')
    out_path.write_text(out)
    print(f'{out_path}: {len(slides)} slides, {len(out)} bytes, from {commit}')


if __name__ == '__main__':
    main()
