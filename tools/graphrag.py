#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-11 — "ok. Tehdään C, ja järjestetään se siten että graafi on toistaiseksi vain itseviittaava … Ja ajetaan pilotti." — card:graphrag-c.md
"""A subject graph over the tree's documents, extracted by a model — self-referential until it earns a citer.

    python tools/graphrag.py pilot                 ten files, two models, one prompt; the sheet is doc/trial/graphrag-pilot.md
    python tools/graphrag.py pilot --dry-run       the files, the sizes and the prompt, no call made
    python tools/graphrag.py check                 the door rule: nothing outside doc/graph/ cites into it
    python tools/graphrag.py extract --backend cli --workers 4    every document, chunked, one call per chunk, cached
    python tools/graphrag.py extract --dry-run     the files, the chunks and the token estimate, no call made
    python tools/graphrag.py lookup <name>         the local read: one entity across every document, its relations, no model
    python tools/graphrag.py entities [--top N]    the entities most documents name

`card:graphrag-c.md`.  Built so far: the door, the pilot, `extract`;
`communities`, `summarise` and `query` follow in that order, each when
the one before has earned it.  `extract`'s store is
`~/.cache/gestate/graphrag/extract-<arm>-<backend>.json` — outside the
tree, the card's Q1 default — one record per chunk, rewritten whole
at the end of every run from the per-call cache, so a run interrupted
halfway loses nothing but the time.

**Nothing this tool produces is evidence.**  An extraction is a model's
reading of a file; a summary is a model's reading of extractions.  The
door rule is what keeps that true mechanically: `test/test_graphrag.py`
refuses a commit in which any file outside `doc/graph/` cites a file
inside it other than `doc/graph/README.md`.

**Two backends, one cache.**  `--backend api` reaches the Messages API
with the standard library, `urllib`, billed to the key in
`ANTHROPIC_API_KEY` at list price.  `--backend cli` runs `claude -p`
headless with that key *unset*, so it is billed to the claude.ai
subscription's usage instead of dollars — measured 2026-09-11: with
the key set the CLI bills the key and adds its 13.9k-token default
system prompt to every call; with the key unset and `--system-prompt`
it authenticates by the login and still carries about 7.9k tokens of
its own per call, three to eight times the raw call's input.  So the
CLI is cheaper in money and dearer in tokens, and the tokens come out
of the same pot as an interactive sitting.  Neither backend lets the
CLI's temperature be set, so a CLI extraction is not reproducible
except from the cache.
Every response is cached under `~/.cache/gestate/graphrag/` by model and
by the hash of prompt and text, so a rerun costs nothing and a changed
prompt costs everything — which is the honest price of a changed
prompt.

**Prices are assumptions, and say so.**  `PRICES` is what the session
remembered on 2026-09-11 for Haiku 4.5 and Sonnet 4.5; the API returns
tokens, not dollars, and the number printed as cost is tokens times
that table.  Correct the table from the pricing page before trusting a
cost line.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

GRAPH_DIR = "doc/graph/"
DOOR = "doc/graph/README.md"

MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-5",
}
#: Sampling parameters per model.  Sonnet 5 refuses `temperature`
#: ("deprecated for this model", HTTP 400, 2026-09-11), so it runs at
#: the API's default and Haiku 4.5 at 0 — the one place the pilot's
#: arms differ, and the sheet's after-run section says so.
PARAMS = {
    "haiku": {"temperature": 0},
    "sonnet": {},
}
#: The CLI has no temperature; what it has is `--effort`, and at the
#: default a Haiku extraction of a 2 kB memory spent 9,400 thinking
#: tokens and 73 s (2026-09-11).  Low effort is what an extraction
#: wants: the prompt is the whole instruction.
CLI_PARAMS = {"effort": "low"}
#: USD per million tokens, (input, output).  Remembered, not fetched —
#: see the module docstring.
PRICES = {
    "haiku": (1.0, 5.0),
    "sonnet": (3.0, 15.0),
}

#: The pilot's ten, chosen before the run for kind and size — three
#: memories, two cards, two specs, the method page, a notes page, the
#: keeper's page; each under 24 kB so nothing is truncated.
#: A card is named by its id, never its shelf (`board/README.md`
#: §"How a card is cited"); `path_of` finds the shelf at run time.
PILOT = [
    "doc/memory/the-evaluation-loop.md",
    "doc/memory/mechanism-not-instructions.md",
    "doc/memory/capacity-is-not-a-caller.md",
    "card:the-first-jam.md",
    "card:standing-questions.md",
    "spec/rules.md",
    "spec/gates.md",
    "doc/method.md",
    "doc/notes/notes-on-the-name.md",
    "keeper.md",
]
MAX_CHARS = 24_000
#: The output ceiling.  4096 cut Sonnet off on 7 of the pilot's 10
#: files on 2026-09-11 (it writes two to three times Haiku's output for
#: the same file), so the ceiling is high and a reply that still hits
#: it is printed as TRUNCATED rather than scored as empty.
MAX_TOKENS = 16_384

PROMPT_VERSION = "2026-09-11a"
TYPES = ("person", "session", "document", "tool", "test", "rule", "defect",
         "card", "memory", "concept", "project", "event")
SYSTEM = f"""You extract a knowledge graph from one document of a software project's repository.

Return ONLY a JSON object, no prose, of the form:
{{"entities": [{{"name": "...", "type": "...", "description": "..."}}],
 "relations": [{{"source": "...", "target": "...", "description": "...", "strength": 1-10}}]}}

Rules:
- An entity is something the document names: a person, a tool, a file, a rule, a defect number, a card, a memory, a concept, a project, an event.
- "type" is one of: {", ".join(TYPES)}.
- Use the document's own name for each entity, verbatim where possible (file paths as written, F-numbers as written, people as named).
- Do not invent entities the document does not mention.
- A relation joins two entities you listed, with one sentence saying how, and a strength from 1 (mentioned together) to 10 (one defines the other).
- Descriptions are one or two sentences, in the document's own terms.
"""


SHELVES = ("board", "board/done", "board/later", "board/refused")


def path_of(rel: str) -> Path:
    """A tree path, or a `card:<name>.md` id resolved to whichever shelf
    holds it today."""
    if rel.startswith("card:"):
        for shelf in SHELVES:
            p = ROOT / shelf / rel[5:]
            if p.exists():
                return p
        sys.exit(f"graphrag: no shelf holds {rel}")
    return ROOT / rel


# --- the API, with the standard library -------------------------------------

BACKENDS = ("api", "cli")


def cache_dir() -> Path:
    home = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return home / "gestate" / "graphrag"


def call(model_key: str, text: str, max_tokens: int = MAX_TOKENS, backend: str = "api") -> dict:
    """One extraction call, cached.  Returns `{"text", "usage", "model", "stop_reason", "cached"}`."""
    model = MODELS[model_key]
    params = PARAMS.get(model_key, {}) if backend == "api" else CLI_PARAMS
    key = hashlib.sha1(f"{model}\n{backend}\n{PROMPT_VERSION}\n{max_tokens}\n{json.dumps(params, sort_keys=True)}\n{SYSTEM}\n{text}".encode()).hexdigest()
    cp = cache_dir() / backend / model_key / f"{key}.json"
    if cp.exists():
        out = json.loads(cp.read_text(encoding="utf-8"))
        out["cached"] = True
        return out
    if backend == "cli":
        out = _call_cli(model_key, text)
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        return out
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("graphrag: ANTHROPIC_API_KEY is not set — tools/toolbox.sh says so too")
    body = {
        "model": model,
        "max_tokens": max_tokens,
        **params,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": text}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode(),
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        sys.exit(f"graphrag: {model} returned HTTP {e.code}: {detail}")
    out = {
        "model": resp.get("model", model),
        "text": "".join(b.get("text", "") for b in resp.get("content", [])),
        "usage": resp.get("usage", {}),
        "stop_reason": resp.get("stop_reason"),
        "seconds": round(time.time() - t0, 1),
        "cached": False,
    }
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def _call_cli(model_key: str, text: str) -> dict:
    """`claude -p`, headless, the API key unset so the subscription pays,
    no tools, our system prompt in place of the CLI's own."""
    import subprocess
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = ["claude", "-p", "--model", model_key, "--output-format", "json",
           "--no-session-persistence", "--tools", "", "--system-prompt", SYSTEM,
           "--effort", CLI_PARAMS["effort"]]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, input=text, capture_output=True, text=True, env=env, timeout=600)
    except FileNotFoundError:
        sys.exit("graphrag: `claude` is not on PATH — the cli backend needs Claude Code installed")
    raw = r.stdout
    i = raw.find("{")
    try:
        d = json.loads(raw[i:]) if i >= 0 else {}
    except json.JSONDecodeError:
        d = {}
    if r.returncode != 0 or d.get("is_error") or "result" not in d:
        sys.exit(f"graphrag: claude -p failed (exit {r.returncode}): {(r.stderr or raw)[:500]}")
    u = d.get("usage", {})
    return {
        "model": next(iter(d.get("modelUsage", {})), MODELS[model_key]),
        "text": d["result"],
        "usage": {"input_tokens": u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                  + u.get("cache_read_input_tokens", 0),
                  "output_tokens": u.get("output_tokens", 0),
                  "cli_overhead_tokens": u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)},
        "stop_reason": d.get("stop_reason"),
        "seconds": round(time.time() - t0, 1),
        "cli_cost_usd_list": d.get("total_cost_usd"),
        "cached": False,
    }


# --- reading what came back --------------------------------------------------

def parse(text: str) -> dict:
    """The JSON object in a reply, with or without prose around it."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        return {"entities": [], "relations": [], "parse_error": "no object"}
    try:
        obj = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        return {"entities": [], "relations": [], "parse_error": str(e)}
    obj.setdefault("entities", [])
    obj.setdefault("relations", [])
    return obj


def norm(name: str) -> str:
    n = name.strip().lower().strip("`*_\"' ")
    n = re.sub(r"\.md$", "", n)
    n = re.sub(r"^(card:|\[\[|doc/memory/)", "", n).rstrip("]")
    return re.sub(r"\s+", " ", n)


def grounded(name: str, text: str) -> bool:
    """The name occurs in the text, or every word of it longer than two
    letters does — case-insensitive.  The mechanical judge of the
    sheet's *invented* question."""
    t = text.lower()
    n = norm(name) or name.strip().lower()      # a name that *is* a stripped prefix, like `doc/memory/`
    if n and n in t:
        return True
    words = [w for w in re.findall(r"[\w-]+", n) if len(w) > 2]
    return bool(words) and all(w in t for w in words)


def cost(model_key: str, usage: dict) -> float:
    pin, pout = PRICES[model_key]
    return (usage.get("input_tokens", 0) * pin + usage.get("output_tokens", 0) * pout) / 1e6


# --- the documents, chunked --------------------------------------------------

DOC_ROOTS = ("doc", "spec", "board", "journal")
CHUNK_CHARS = 12_000            # about three thousand tokens
SKIP_DIRS = {"target", ".venv", "__pycache__", ".git", "node_modules", ".claude"}


def documents() -> list[str]:
    """Every `.md` under the document roots and at the root, sorted;
    never anything under `doc/graph/` (the door works both ways) and
    never the pilot's own outputs."""
    out = []
    for p in sorted(ROOT.glob("*.md")):
        out.append(p.name)
    for top in DOC_ROOTS:
        for p in sorted((ROOT / top).rglob("*.md")):
            rel = p.relative_to(ROOT).as_posix()
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if rel.startswith(GRAPH_DIR) or "/graphrag-pilot/" in rel:
                continue
            out.append(rel)
    return out


def chunks(text: str, size: int = CHUNK_CHARS) -> list[str]:
    """Paragraph-bounded pieces of at most `size` characters; a single
    paragraph longer than that is cut at a line."""
    out, cur = [], ""
    for para in text.split("\n\n"):
        piece = para + "\n\n"
        if len(cur) + len(piece) > size and cur:
            out.append(cur)
            cur = ""
        while len(piece) > size:
            cut = piece.rfind("\n", 0, size)
            cut = cut if cut > 0 else size
            out.append(cur + piece[:cut])
            cur, piece = "", piece[cut:]
        cur += piece
    if cur.strip():
        out.append(cur)
    return out


def jobs() -> list[tuple[str, int, int, str]]:
    """`(rel, i, n, text)` for every chunk of every document."""
    out = []
    for rel in documents():
        text = (ROOT / rel).read_text(encoding="utf-8")
        cs = chunks(text)
        for i, c in enumerate(cs):
            out.append((rel, i, len(cs), c))
    return out


def _prompt(rel: str, i: int, n: int, text: str) -> str:
    where = f"Document `{rel}`" if n == 1 else f"Document `{rel}`, part {i + 1} of {n}"
    return f"{where}:\n\n{text}"


def extract(arm: str, backend: str, workers: int, limit: int | None, dry_run: bool) -> int:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    js = jobs()
    total_chars = sum(len(j[3]) for j in js)
    print(f"extract: {len(documents())} documents, {len(js)} chunks, {total_chars/1e6:.2f} M chars "
          f"≈ {total_chars/4/1e6:.2f} M tokens, arm {arm}, backend {backend}, {workers} workers")
    if dry_run:
        by_top = {}
        for rel, _i, _n, text in js:
            top = rel.split("/")[0] if "/" in rel else "(root)"
            by_top[top] = by_top.get(top, 0) + len(text)
        for k, v in sorted(by_top.items(), key=lambda kv: -kv[1]):
            print(f"  {k:10s} {v/1e6:.2f} M chars")
        return 0
    if limit:
        js = js[:limit]
    store_path = cache_dir() / f"extract-{arm}-{backend}.json"
    records: dict[str, dict] = {}
    if store_path.exists():
        try:
            records = {r["id"]: r for r in json.loads(store_path.read_text(encoding="utf-8"))["records"]}
        except (OSError, ValueError, KeyError):
            records = {}
    t_start = time.time()
    done_fresh, secs_fresh, in_tok, out_tok = 0, 0.0, 0, 0
    estimate_printed = False

    def one(job):
        rel, i, n, text = job
        r = call(arm, _prompt(rel, i, n, text), backend=backend)
        obj = parse(r["text"])
        ents = [e for e in obj["entities"] if isinstance(e, dict) and e.get("name")]
        return {
            "id": f"{rel}#{i}", "file": rel, "chunk": i, "of": n, "chars": len(text),
            "model": r["model"], "usage": r["usage"], "seconds": r.get("seconds"),
            "cached": r["cached"], "stop_reason": r.get("stop_reason"),
            "parse_error": obj.get("parse_error"),
            "entities": [{"name": e["name"], "norm": norm(e["name"]), "type": e.get("type"),
                          "description": e.get("description", ""),
                          "grounded": grounded(e["name"], text)} for e in ents],
            "relations": [x for x in obj["relations"] if isinstance(x, dict)],
        }

    def flush():
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text(json.dumps({"arm": arm, "backend": backend, "prompt": PROMPT_VERSION,
                                          "written": time.strftime("%Y-%m-%d %H:%M"),
                                          "records": list(records.values())},
                                         ensure_ascii=False), encoding="utf-8")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, j): j for j in js}
        for k, fut in enumerate(as_completed(futures), 1):
            rec = fut.result()
            records[rec["id"]] = rec
            u = rec["usage"]
            in_tok += u.get("input_tokens", 0)
            out_tok += u.get("output_tokens", 0)
            if not rec["cached"]:
                done_fresh += 1
                secs_fresh += rec["seconds"] or 0
            g = sum(1 for e in rec["entities"] if e["grounded"])
            took = "  (cached)" if rec["cached"] else f"  {rec['seconds'] or 0:5.1f}s"
            print(f"  {k:4d}/{len(js)} {rec['id']:56s} ents {len(rec['entities']):3d} grounded {g:3d} "
                  f"in {u.get('input_tokens', 0):6d} out {u.get('output_tokens', 0):5d}{took}"
                  f"{'  TRUNCATED' if rec['stop_reason'] == 'max_tokens' else ''}"
                  f"{'  PARSE ERROR' if rec['parse_error'] else ''}", flush=True)
            if done_fresh == 10 and not estimate_printed:
                estimate_printed = True
                per = secs_fresh / done_fresh
                remaining = len(js) - k
                print(f"  --- after 10 fresh calls: {per:.1f} s each, {in_tok/k:.0f} in + {out_tok/k:.0f} out tokens each; "
                      f"{remaining} left ≈ {remaining*per/workers/60:.0f} min at {workers} workers, "
                      f"≈ {remaining*in_tok/k/1e6:.2f} M in + {remaining*out_tok/k/1e6:.2f} M out ---", flush=True)
            if k % 25 == 0:
                flush()
    flush()
    ents = sum(len(r["entities"]) for r in records.values())
    gr = sum(1 for r in records.values() for e in r["entities"] if e["grounded"])
    errs = sum(1 for r in records.values() if r["parse_error"])
    trunc = sum(1 for r in records.values() if r["stop_reason"] == "max_tokens")
    print(f"extract: {len(records)} records, {ents} entities ({gr/ents:.3f} grounded), "
          f"{sum(len(r['relations']) for r in records.values())} relations, "
          f"{errs} parse errors, {trunc} truncated; tokens in {in_tok} out {out_tok}; "
          f"{done_fresh} fresh calls in {(time.time()-t_start)/60:.1f} min; store {store_path}")
    return 0


# --- reading the graph: the local move, no model -----------------------------

def load_store(arm: str = "haiku", backend: str = "cli") -> dict:
    sp = cache_dir() / f"extract-{arm}-{backend}.json"
    if not sp.exists():
        sys.exit(f"graphrag: no store at {sp} — run `extract` first")
    return json.loads(sp.read_text(encoding="utf-8"))


def merged(store: dict) -> dict[str, dict]:
    """Entities merged across chunks by normalised name: every
    description, every type the models gave, every document, and every
    relation touching it."""
    ents: dict[str, dict] = {}
    for rec in store["records"]:
        for e in rec["entities"]:
            m = ents.setdefault(e["norm"], {"names": Counter(), "types": Counter(), "docs": set(),
                                            "descriptions": [], "relations": []})
            m["names"][e["name"]] += 1
            if e.get("type"):
                m["types"][e["type"]] += 1
            m["docs"].add(rec["file"])
            if e.get("description"):
                m["descriptions"].append((rec["file"], e["description"]))
        for r in rec["relations"]:
            a, b = norm(str(r.get("source", ""))), norm(str(r.get("target", "")))
            for side, other in ((a, b), (b, a)):
                if side in ents:
                    ents[side]["relations"].append((rec["file"], other, r.get("description", ""), r.get("strength")))
    return ents


def lookup(name: str, arm: str, backend: str, limit: int) -> int:
    store = load_store(arm, backend)
    ents = merged(store)
    key = norm(name)
    hits = [k for k in ents if k == key] or sorted((k for k in ents if key in k), key=lambda k: -len(ents[k]["docs"]))
    if not hits:
        print(f"lookup: nothing named like `{name}` in {len(ents)} entities from {len(store['records'])} chunks")
        return 1
    print(f"(store: {len(store['records'])} chunks, {len(ents)} entities, written {store['written']} — "
          f"a model's reading, not evidence)")
    for k in hits[:limit]:
        m = ents[k]
        name_shown = m["names"].most_common(1)[0][0]
        print(f"\n== {name_shown}  [{', '.join(t for t, _ in m['types'].most_common(3))}]  "
              f"in {len(m['docs'])} document(s)")
        for f, d in m["descriptions"][:6]:
            print(f"   {f}: {d[:160]}")
        rels = sorted(m["relations"], key=lambda r: -(r[3] or 0))
        seen = set()
        for f, other, d, st in rels:
            if other in seen:
                continue
            seen.add(other)
            print(f"   -> {other}  ({st})  {d[:110]}   [{f}]")
            if len(seen) >= 12:
                break
        docs = sorted(m["docs"])
        print(f"   documents: {', '.join(docs[:12])}{' …' if len(docs) > 12 else ''}")
    if len(hits) > limit:
        print(f"\n… and {len(hits) - limit} more names containing `{name}`")
    return 0


def entities_top(arm: str, backend: str, top: int) -> int:
    store = load_store(arm, backend)
    ents = merged(store)
    print(f"(store: {len(store['records'])} chunks, {len(ents)} entities, written {store['written']})")
    for k, m in sorted(ents.items(), key=lambda kv: -len(kv[1]["docs"]))[:top]:
        print(f"  {len(m['docs']):4d} docs  {m['names'].most_common(1)[0][0]:50s} [{m['types'].most_common(1)[0][0] if m['types'] else '?'}]")
    return 0


# --- the door ----------------------------------------------------------------

def intruders(index: dict) -> list[tuple[str, int, str]]:
    """`(citer, line, target)` for every citation from outside
    `doc/graph/` to a file inside it other than the README."""
    out = []
    for rel, entry in index.items():
        if rel.startswith(GRAPH_DIR):
            continue
        for line, key, _text, _explicit in entry.get("c", []):
            if key.startswith(GRAPH_DIR) and key != DOOR:
                out.append((rel, line, key))
    return sorted(out)


def check() -> int:
    import backlinks
    tree = backlinks.Tree(ROOT)
    bad = intruders(backlinks.index(tree))
    if not bad:
        print(f"graphrag: the door holds — nothing outside {GRAPH_DIR} cites into it"
              + ("" if (ROOT / GRAPH_DIR).exists() else " (and it does not exist yet)"))
        return 0
    for rel, line, key in bad:
        print(f"  {rel}:{line} cites {key}")
    print(f"graphrag: {len(bad)} citation(s) into {GRAPH_DIR} from outside — card:graphrag-c.md says why not")
    return 1


# --- the pilot ---------------------------------------------------------------

def pilot(dry_run: bool, arms: list[str], out_dir: Path, backend: str = "api", n_files: int | None = None) -> int:
    files = []
    for rel in PILOT[:n_files]:
        text = path_of(rel).read_text(encoding="utf-8")
        cut = len(text) > MAX_CHARS
        files.append((rel, text[:MAX_CHARS], cut))
        print(f"  {rel:48s} {len(text):6d} chars{'  TRUNCATED' if cut else ''}")
    if dry_run:
        print("\n--- system prompt ---\n" + SYSTEM)
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, dict]] = {a: {} for a in arms}
    for rel, text, _cut in files:
        for arm in arms:
            r = call(arm, f"Document `{rel}`:\n\n{text}", backend=backend)
            obj = parse(r["text"])
            ents = obj["entities"]
            names = [e.get("name", "") for e in ents if isinstance(e, dict)]
            g = [grounded(n, text) for n in names]
            rec = {
                "file": rel, "model": r["model"], "usage": r["usage"], "seconds": r.get("seconds"),
                "cached": r["cached"], "stop_reason": r.get("stop_reason"),
                "entities": len(ents), "relations": len(obj["relations"]),
                "grounded": sum(g), "parse_error": obj.get("parse_error"),
                "names": sorted({norm(n) for n in names if n}),
                "ungrounded": sorted({n for n, ok in zip(names, g) if not ok}),
                "raw": obj,
            }
            results[arm][rel] = rec
            slug = re.sub(r"[^\w]+", "-", rel).strip("-")
            (out_dir / f"{arm}-{slug}.json").write_text(
                json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {arm:6s} {rel:40s} ents {rec['entities']:3d} rel {rec['relations']:3d} "
                  f"grounded {rec['grounded']}/{rec['entities']}  "
                  f"in {r['usage'].get('input_tokens', 0)} out {r['usage'].get('output_tokens', 0)}"
                  f"{'  (cached)' if r['cached'] else ''}"
                  f"{'  TRUNCATED at max_tokens' if r.get('stop_reason') == 'max_tokens' else ''}"
                  f"{'  PARSE ERROR: ' + rec['parse_error'] if rec['parse_error'] else ''}")

    print("\n--- the sheet's numbers ---")
    summary = {}
    for arm in arms:
        rs = results[arm].values()
        ents = sum(r["entities"] for r in rs)
        gr = sum(r["grounded"] for r in rs)
        usage_in = sum(r["usage"].get("input_tokens", 0) for r in rs)
        usage_out = sum(r["usage"].get("output_tokens", 0) for r in rs)
        c = sum(cost(arm, r["usage"]) for r in rs)
        summary[arm] = {"entities": ents, "relations": sum(r["relations"] for r in rs),
                        "grounded": round(gr / ents, 3) if ents else None,
                        "input_tokens": usage_in, "output_tokens": usage_out,
                        "cost_usd_assumed": round(c, 3),
                        "parse_errors": sum(1 for r in rs if r["parse_error"]),
                        "truncated": sum(1 for r in rs if r.get("stop_reason") == "max_tokens")}
        print(f"{arm:6s} entities {ents:4d}  relations {summary[arm]['relations']:4d}  "
              f"grounded {summary[arm]['grounded']}  tokens in {usage_in} out {usage_out}  "
              f"cost ≈ ${c:.3f} (assumed prices)  parse errors {summary[arm]['parse_errors']}  "
              f"truncated {summary[arm]['truncated']}")
    if len(arms) == 2:
        a, b = arms
        jac = []
        for rel, _t, _c in files:
            sa, sb = set(results[a][rel]["names"]), set(results[b][rel]["names"])
            jac.append(len(sa & sb) / len(sa | sb) if sa | sb else 1.0)
        summary["overlap_jaccard_mean"] = round(sum(jac) / len(jac), 3)
        summary["overlap_jaccard_min"] = round(min(jac), 3)
        print(f"overlap of entity names {a}∩{b}: Jaccard mean {summary['overlap_jaccard_mean']}, "
              f"min {summary['overlap_jaccard_min']}")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"raw outputs and summary.json in {out_dir.relative_to(ROOT) if out_dir.is_relative_to(ROOT) else out_dir}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pilot", help="ten files, two models, one prompt")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--arms", default="haiku,sonnet")
    p.add_argument("--out", default=str(ROOT / "doc" / "trial" / "graphrag-pilot"))
    p.add_argument("--backend", choices=BACKENDS, default="api",
                   help="api: the key pays at list price; cli: claude -p, the subscription pays in usage")
    p.add_argument("--files", type=int, default=len(PILOT), help="only the first N pilot files")
    sub.add_parser("check", help="the door rule")
    e = sub.add_parser("extract", help="every document, chunked, one call per chunk, cached")
    e.add_argument("--dry-run", action="store_true")
    e.add_argument("--arm", default="haiku", choices=list(MODELS))
    e.add_argument("--backend", choices=BACKENDS, default="cli")
    e.add_argument("--workers", type=int, default=4)
    e.add_argument("--limit", type=int, help="only the first N chunks")
    l = sub.add_parser("lookup", help="one entity across every document — the local read, no model")
    l.add_argument("name")
    l.add_argument("--arm", default="haiku", choices=list(MODELS))
    l.add_argument("--backend", choices=BACKENDS, default="cli")
    l.add_argument("--limit", type=int, default=3)
    t = sub.add_parser("entities", help="the entities most documents name")
    t.add_argument("--arm", default="haiku", choices=list(MODELS))
    t.add_argument("--backend", choices=BACKENDS, default="cli")
    t.add_argument("--top", type=int, default=30)
    a = ap.parse_args(argv)
    if a.cmd == "check":
        return check()
    if a.cmd == "lookup":
        return lookup(a.name, a.arm, a.backend, a.limit)
    if a.cmd == "entities":
        return entities_top(a.arm, a.backend, a.top)
    if a.cmd == "extract":
        return extract(a.arm, a.backend, a.workers, a.limit, a.dry_run)
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]
    for x in arms:
        if x not in MODELS:
            sys.exit(f"graphrag: unknown arm `{x}`; known: {', '.join(MODELS)}")
    return pilot(a.dry_run, arms, Path(a.out), a.backend, a.files)


if __name__ == "__main__":
    sys.exit(main())
