#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-11 — "ok. Tehdään C, ja järjestetään se siten että graafi on toistaiseksi vain itseviittaava … Ja ajetaan pilotti." — card:graphrag-c.md
"""A subject graph over the tree's documents, extracted by a model — self-referential until it earns a citer.

    python tools/graphrag.py pilot                 ten files, two models, one prompt; the sheet is doc/trial/graphrag-pilot.md
    python tools/graphrag.py pilot --dry-run       the files, the sizes and the prompt, no call made
    python tools/graphrag.py check                 the door rule, and how many chunks a run would still have to call
    python tools/graphrag.py extract --backend api --workers 6 --budget 12    every document, chunked, one call per chunk, cached; stops at $12
    python tools/graphrag.py extract --backend cli --workers 4               the same, billed to the subscription; finds the api run's replies
    python tools/graphrag.py extract --dry-run     the files, the chunks and the token estimate, no call made
    python tools/graphrag.py stop                  ask a running extract to finish its calls in flight and exit
    python tools/graphrag.py lookup <name>         the local read: one entity across every document, its relations, no model
    python tools/graphrag.py entities [--top N] [--type T]    the entities most documents name
    python tools/graphrag.py subjects              item 1: well-cited subjects nothing in the tree titles — no model
    python tools/graphrag.py contradictions        item 2: numbers about one subject that disagree across documents — no model
    python tools/graphrag.py query "<question>"    the global search, LightRAG's shape: two calls, printed, never written
    python tools/graphrag.py cue <path>            item 4: what the backlinks hook adds for this file — no model

`card:graphrag-c.md`.  Built so far: the door, the pilot, `extract`,
`lookup` and `entities`.  What follows is `query`, the dual-level
retrieval of LightRAG (Guo et al., arXiv 2410.05779) — keywords from
the question, matched to entity names and to the keywords on
relations, one hop, one generation call — in place of communities,
summaries and a map-reduce over them; Henri's decision 2026-09-12,
the card's §"LightRAG instead of summaries".  `extract`'s store is
`~/.cache/gestate/graphrag/extract-<arm>.json` — outside the tree, the
card's Q1 default — one record per chunk, rewritten whole
at the end of every run from the per-call cache, so a run interrupted
halfway loses nothing but the time.

**Nothing this tool produces is evidence.**  An extraction is a model's
reading of a file; a summary is a model's reading of extractions.  The
door rule is what keeps that true mechanically: `test/test_graphrag.py`
refuses a commit in which any file outside `doc/graph/` cites a file
inside it other than `doc/graph/README.md`.

**Two backends, one cache — and the cache does not know which.**
Since 2026-09-12 a reply is keyed by model, prompt version, ceiling
and text, not by backend, so the first run on the API and the
week's increments on the CLI fill one cache and one store; each
reply and each record says which backend produced it.  Henri's ask,
the same morning: *"I'd want to use api backend with haiku and 6
workers, then later, do the incremental updates with cli."*  The two
backends sample differently (temperature 0 against `--effort low`),
which the record keeps and the graph does not mind.
`--backend api` reaches the Messages API
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

#: A changed prompt re-extracts everything, so the version is bumped by
#: hand.  2026-09-12a: relations carry `keywords`, the field LightRAG's
#: high-level retrieval matches a question's themes against; bumped
#: while 49 of 535 chunks were paid for, which is when it costs least.
PROMPT_VERSION = "2026-09-12a"
TYPES = ("person", "session", "document", "tool", "test", "rule", "defect",
         "card", "memory", "concept", "project", "event")
SYSTEM = f"""You extract a knowledge graph from one document of a software project's repository.

Return ONLY a JSON object, no prose, of the form:
{{"entities": [{{"name": "...", "type": "...", "description": "..."}}],
 "relations": [{{"source": "...", "target": "...", "description": "...", "keywords": ["..."], "strength": 1-10}}]}}

Rules:
- An entity is something the document names: a person, a tool, a file, a rule, a defect number, a card, a memory, a concept, a project, an event.
- "type" is one of: {", ".join(TYPES)}.
- Use the document's own name for each entity, verbatim where possible (file paths as written, F-numbers as written, people as named).
- Do not invent entities the document does not mention.
- A relation joins two entities you listed, with one sentence saying how, and a strength from 1 (mentioned together) to 10 (one defines the other).
- "keywords" on a relation are one to three short phrases naming the theme the relation is about, at the level a question would use — "testing standard", "commit rights", "audio teardown" — not the entity names again.
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


def cache_path_for(model_key: str, text: str, max_tokens: int = MAX_TOKENS, system: str = SYSTEM) -> Path:
    """Where one call's reply lives: model, prompt version, ceiling and
    the text itself key it — not the backend, so a reply made on the
    API is found by a run on the CLI and the other way round — and a
    changed file or a changed prompt is a fresh call and nothing else is."""
    key = hashlib.sha1(f"{MODELS[model_key]}\n{PROMPT_VERSION}\n{max_tokens}\n{system}\n{text}".encode()).hexdigest()
    return cache_dir() / model_key / f"{key}.json"


def call(model_key: str, text: str, max_tokens: int = MAX_TOKENS, backend: str = "api", system: str = SYSTEM,
         expect_json: bool = True) -> dict:
    """One call, cached.  Returns `{"text", "usage", "model", "stop_reason", "cached"}`.
    `system` is the extraction prompt unless the caller is `query`, and
    `expect_json` is what the cli backend judges a reply by."""
    model = MODELS[model_key]
    params = PARAMS.get(model_key, {}) if backend == "api" else CLI_PARAMS
    cp = cache_path_for(model_key, text, max_tokens, system)
    if cp.exists():
        out = json.loads(cp.read_text(encoding="utf-8"))
        out["cached"] = True
        return out
    if backend == "cli":
        out = {**_call_cli(model_key, text, system, expect_json), "backend": "cli"}
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
        "system": system,
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
        if e.code in (429, 529, 500, 502, 503) and _retries_left(model_key, text):
            return call(model_key, text, max_tokens, backend, system)
        sys.exit(f"graphrag: {model} returned HTTP {e.code}: {detail}")
    out = {
        "model": resp.get("model", model),
        "text": "".join(b.get("text", "") for b in resp.get("content", [])),
        "usage": resp.get("usage", {}),
        "stop_reason": resp.get("stop_reason"),
        "seconds": round(time.time() - t0, 1),
        "cached": False,
        "backend": "api",
    }
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


_RETRIES: dict[str, int] = {}


def _retries_left(model_key: str, text: str) -> bool:
    """Three retries per call, 30/90/240 s apart, for a rate limit or an
    overloaded model on the api backend."""
    k = hashlib.sha1(f"{model_key}\n{text}".encode()).hexdigest()
    n = _RETRIES.get(k, 0)
    if n >= 3:
        return False
    _RETRIES[k] = n + 1
    print(f"  retry {n + 1}/3 in {(30, 90, 240)[n]} s", file=sys.stderr, flush=True)
    time.sleep((30, 90, 240)[n])
    return True


def cli_reply_ok(returncode: int, d: dict, expect_json: bool) -> bool:
    """A reply is a reply only if the model was asked: tokens out, a
    result, and — for an extraction — an object in it.  Anything else, a
    hook's refusal, an empty result, a usage-limit page, is a failure to
    retry and never a thing to cache.  An answer is prose (2026-09-12,
    when `query` moved to the cli), so the object is asked for only when
    the caller expects one."""
    u = d.get("usage", {})
    result = d.get("result", "")
    return (returncode == 0 and not d.get("is_error") and isinstance(result, str)
            and u.get("output_tokens", 0) > 0 and bool(result.strip())
            and (not expect_json or "{" in result))


def _call_cli(model_key: str, text: str, system: str = SYSTEM, expect_json: bool = True) -> dict:
    """`claude -p`, headless, the API key unset so the subscription pays,
    no tools, our system prompt in place of the CLI's own."""
    import subprocess
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = ["claude", "-p", "--model", model_key, "--output-format", "json",
           "--no-session-persistence", "--tools", "", "--system-prompt", system,
           "--effort", CLI_PARAMS["effort"]]
    #: **Run it outside the project.**  A headless `claude -p` started in
    #: this checkout inherits `.claude/settings.json`'s hooks, and on
    #: 2026-09-11 the sitting limit (`tools/limit.sh --hook`,
    #: UserPromptSubmit) blocked every call from 20:48 on — 276 replies
    #: that were the hook's message, cached as extractions.  The cache
    #: directory is a working directory with no hooks.
    cwd = cache_dir()
    cwd.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    #: A four-hour run must not die on one refused call: a rate limit, a
    #: hiccup, an overloaded model.  Three tries, backing off, then out
    #: loud with the last reply — never a silent empty record.
    last = ""
    for attempt, wait in enumerate((0, 30, 90, 240)):
        if wait:
            time.sleep(wait)
        try:
            r = subprocess.run(cmd, input=text, capture_output=True, text=True, env=env, timeout=900, cwd=cwd)
        except FileNotFoundError:
            sys.exit("graphrag: `claude` is not on PATH — the cli backend needs Claude Code installed")
        except subprocess.TimeoutExpired:
            last = "timeout after 900 s"
            continue
        raw = r.stdout
        i = raw.find("{")
        try:
            d = json.loads(raw[i:]) if i >= 0 else {}
        except json.JSONDecodeError:
            d = {}
        result = d.get("result", "")
        if cli_reply_ok(r.returncode, d, expect_json):
            break
        last = f"exit {r.returncode}: {(r.stderr or result or raw)[:300]}"
        print(f"  retry {attempt + 1}/3 after {last[:80]}", file=sys.stderr, flush=True)
    else:
        sys.exit(f"graphrag: claude -p failed four times; last: {last}")
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
        return salvage(text[start:end + 1], str(e))
    obj.setdefault("entities", [])
    obj.setdefault("relations", [])
    return obj


def salvage(body: str, error: str) -> dict:
    """What a reply that is not JSON still holds: every innermost
    `{…}` that parses on its own, sorted by its keys into an entity or a
    relation.  2026-09-12, chunk 80 of the api run: one relation closed
    after its description and went on writing keywords outside it, and
    the whole chunk — 30-odd entities — was scored as empty.  The error
    is kept on the record, with what was recovered, so the lamp still
    shows and the graph still has the chunk."""
    ents, rels = [], []
    for m in re.finditer(r"\{[^{}]*\}", body):
        try:
            o = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        if not isinstance(o, dict):
            continue
        if "name" in o:
            ents.append(o)
        elif "source" in o and "target" in o:
            rels.append(o)
    return {"entities": ents, "relations": rels,
            "parse_error": f"{error}; salvaged {len(ents)} entities, {len(rels)} relations"}


def relation(x: dict) -> dict:
    """A relation as the store keeps it: `keywords` a list of non-empty
    strings, whatever shape the model gave it — a string, a list, nothing."""
    kw = x.get("keywords", [])
    if isinstance(kw, str):
        kw = [k for k in re.split(r"[,;]", kw)]
    if not isinstance(kw, list):
        kw = []
    return {**x, "keywords": [str(k).strip() for k in kw if str(k).strip()]}


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
            #: The graph never reads its own outputs: the pilot's, and the
            #: query's answers kept as trial artefacts (2026-09-12).
            if rel.startswith(GRAPH_DIR) or "/graphrag-" in rel:      # the pilot's outputs and every trial's answers: the graph never reads its own
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


def pagerank(adj: dict[str, dict[str, float]], alpha: float = 0.85, iters: int = 50) -> dict[str, float]:
    """PageRank over an undirected adjacency, the power iteration; a node
    with no neighbours gets the teleport share and nothing else."""
    nodes = list(adj)
    if not nodes:
        return {}
    n = len(nodes)
    pr = {v: 1.0 / n for v in nodes}
    for _ in range(iters):
        dangling = sum(pr[v] for v in nodes if not adj[v])      # spread evenly, so the total stays 1
        pr = {v: (1 - alpha + alpha * dangling) / n + alpha * sum(pr[u] / len(adj[u]) for u in adj[v] if adj[u])
              for v in nodes}
    return pr


def centrality() -> dict[str, float]:
    """Every document's PageRank in the tree's own citation graph —
    `tools/communities.py`'s, undirected, built from the backlinks index;
    a document nothing cites and that cites nothing is absent, so 0."""
    import backlinks
    import communities
    adj, _read = communities.graph(backlinks.Tree(ROOT))
    return pagerank(adj)


def jobs() -> list[tuple[str, int, int, str]]:
    """`(rel, i, n, text)` for every chunk of every document, **the most
    central document first** — KET-RAG's observation (Huang, Zhang, Xiao,
    KDD 2025) that a run allowed to extract only part of a corpus should
    take the chunks central to it, applied to the order rather than to a
    fraction: a run that completes is the same graph whatever the order,
    and a run the budget stops has left out the periphery, not the end
    of the alphabet.  Henri, 2026-09-12: "ok. lets do it before I
    start."  Ties, and the documents outside the citation graph, stay
    alphabetical."""
    pr = centrality()
    out = []
    for rel in sorted(documents(), key=lambda rel: (-pr.get(rel, 0.0), rel)):
        text = (ROOT / rel).read_text(encoding="utf-8")
        cs = chunks(text)
        for i, c in enumerate(cs):
            out.append((rel, i, len(cs), c))
    return out


def _prompt(rel: str, i: int, n: int, text: str) -> str:
    where = f"Document `{rel}`" if n == 1 else f"Document `{rel}`, part {i + 1} of {n}"
    return f"{where}:\n\n{text}"


def seed_records(store_path: Path) -> dict[str, dict]:
    """The records a run starts from: the store's, when the store was
    written under this prompt.  A record with no output tokens is a
    refusal that was once cached as a reply (2026-09-11) and is dropped,
    so a rerun re-asks for that chunk instead of carrying the hole.  A
    store from another prompt version is not carried at all (2026-09-12):
    its records lack what the prompt now asks for, and the per-call cache
    still holds every reply, so nothing is lost by starting the store
    over — the old file is renamed beside it, not deleted."""
    if not store_path.exists():
        return {}
    try:
        store = json.loads(store_path.read_text(encoding="utf-8"))
        if store.get("prompt") != PROMPT_VERSION:
            old = store_path.with_name(f"{store_path.stem}.{store.get('prompt') or 'unversioned'}.json")
            store_path.rename(old)
            print(f"extract: the store was written under prompt {store.get('prompt')!r}, not {PROMPT_VERSION!r}; "
                  f"set aside as {old.name} and starting the store over", flush=True)
            return {}
        return {r["id"]: r for r in store["records"] if r.get("usage", {}).get("output_tokens", 0) > 0}
    except (OSError, ValueError, KeyError):
        return {}


def extract(arm: str, backend: str, workers: int, limit: int | None, dry_run: bool,
            budget: float | None = None) -> int:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    js = jobs()
    total_chars = sum(len(j[3]) for j in js)
    print(f"extract: {len(documents())} documents, {len(js)} chunks, {total_chars/1e6:.2f} M chars "
          f"≈ {total_chars/4/1e6:.2f} M tokens, arm {arm}, backend {backend}, {workers} workers")
    if dry_run:
        seen, first = set(), []
        for rel, _i, _n, _text in js:
            if rel not in seen:
                seen.add(rel)
                first.append(rel)
        print("  first by centrality in the citation graph: " + ", ".join(first[:8]))
        print("  last: " + ", ".join(first[-3:]))
        by_top = {}
        for rel, _i, _n, text in js:
            top = rel.split("/")[0] if "/" in rel else "(root)"
            by_top[top] = by_top.get(top, 0) + len(text)
        for k, v in sorted(by_top.items(), key=lambda kv: -kv[1]):
            print(f"  {k:10s} {v/1e6:.2f} M chars")
        return 0
    if limit:
        js = js[:limit]
    store_path = cache_dir() / f"extract-{arm}.json"
    #: The tool writes its own pid, because `$!` behind `nohup` on
    #: 2026-09-11 named the shell and the scheduled kill took that and
    #: not this.
    (cache_dir() / "extract.pid").write_text(f"pid {os.getpid()}\n", encoding="utf-8")
    records = seed_records(store_path)
    t_start = time.time()
    done_fresh, secs_fresh, in_tok, out_tok, spent = 0, 0.0, 0, 0, 0.0
    estimate_printed = False

    def one(job):
        rel, i, n, text = job
        r = call(arm, _prompt(rel, i, n, text), backend=backend)
        obj = parse(r["text"])
        ents = [e for e in obj["entities"] if isinstance(e, dict) and e.get("name")]
        return {
            "id": f"{rel}#{i}", "file": rel, "chunk": i, "of": n, "chars": len(text),
            "model": r["model"], "backend": r.get("backend", backend), "usage": r["usage"], "seconds": r.get("seconds"),
            "cached": r["cached"], "stop_reason": r.get("stop_reason"),
            "parse_error": obj.get("parse_error"),
            "entities": [{"name": e["name"], "norm": norm(e["name"]), "type": e.get("type"),
                          "description": e.get("description", ""),
                          "grounded": grounded(e["name"], text)} for e in ents],
            "relations": [relation(x) for x in obj["relations"] if isinstance(x, dict)],
        }

    def flush():
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text(json.dumps({"arm": arm, "prompt": PROMPT_VERSION,
                                          "written": time.strftime("%Y-%m-%d %H:%M"),
                                          "records": list(records.values())},
                                         ensure_ascii=False), encoding="utf-8")

    #: `stop` touches this; the loop looks between batches, finishes the
    #: calls in flight, flushes and leaves — a kill lost the four in
    #: flight and, once, took the wrong process.
    stop_flag = cache_dir() / "extract.stop"
    stop_flag.unlink(missing_ok=True)
    k = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for start in range(0, len(js), workers):
            if stop_flag.exists():
                print(f"extract: stop asked at chunk {k}/{len(js)} — flushing and leaving; "
                      f"rerun the same command to continue", flush=True)
                stop_flag.unlink(missing_ok=True)
                break
            #: `--budget` is the same stop, pulled by the assumed price
            #: table instead of a hand; the money already spent is not
            #: lost, every reply is in the cache and the store.
            if budget is not None and spent >= budget:
                print(f"extract: budget ${budget:.2f} reached at chunk {k}/{len(js)} (${spent:.2f} at assumed prices) "
                      f"— flushing and leaving; rerun with a higher --budget or --backend cli to continue", flush=True)
                break
            futures = {pool.submit(one, j): j for j in js[start:start + workers]}
            for fut in as_completed(futures):
                k += 1
                rec = fut.result()
                records[rec["id"]] = rec
                u = rec["usage"]
                in_tok += u.get("input_tokens", 0)
                out_tok += u.get("output_tokens", 0)
                if not rec["cached"]:
                    done_fresh += 1
                    secs_fresh += rec["seconds"] or 0
                    if rec["backend"] == "api":
                        spent += cost(arm, u)
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
                          f"≈ {remaining*in_tok/k/1e6:.2f} M in + {remaining*out_tok/k/1e6:.2f} M out"
                          + (f" ≈ ${remaining*spent/done_fresh:.2f} more at assumed prices" if backend == "api" else "")
                          + " ---", flush=True)
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
          f"{done_fresh} fresh calls in {(time.time()-t_start)/60:.1f} min"
          + (f", ${spent:.2f} at assumed prices" if backend == "api" else "")
          + f"; store {store_path}")
    return 0


# --- reading the graph: the local move, no model -----------------------------

def load_store(arm: str = "haiku") -> dict:
    sp = cache_dir() / f"extract-{arm}.json"
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
                    ents[side]["relations"].append((rec["file"], other, r.get("description", ""), r.get("strength"),
                                                    tuple(r.get("keywords") or ())))
    return ents


def lookup(name: str, arm: str, limit: int) -> int:
    store = load_store(arm)
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
        for f, other, d, st, _kw in rels:
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


def entities_top(arm: str, top: int, type_: str | None = None) -> int:
    """The entities most documents name; `--type concept` is the plan's
    item 1 — the top of the unfiltered list is the citation graph again,
    documents and the one person, which backlinks already draws
    (Henri, 2026-09-12, reading the half-built store)."""
    store = load_store(arm)
    ents = merged(store)
    if type_:
        ents = {k: m for k, m in ents.items() if m["types"] and m["types"].most_common(1)[0][0] == type_}
    print(f"(store: {len(store['records'])} chunks, {len(ents)} entities{f' of type {type_}' if type_ else ''}, written {store['written']})")
    for k, m in sorted(ents.items(), key=lambda kv: -len(kv[1]["docs"]))[:top]:
        print(f"  {len(m['docs']):4d} docs  {m['names'].most_common(1)[0][0]:50s} [{m['types'].most_common(1)[0][0] if m['types'] else '?'}]")
    return 0


# --- reading the graph: the two model-free lists, the plan's items 1 and 2 ---

#: The types a subject can have.  A document, tool, card, memory or defect
#: has a home by construction — it is a file or a numbered entry — so
#: item 1 asks only about the kinds that can be named in twenty places
#: and titled in none.
SUBJECT_TYPES = ("concept", "rule", "event", "project")


def headings() -> set[str]:
    """Every name the tree has *titled* something with, normalised: a
    document's path and stem, every markdown heading, every memory-index
    hook.  Being grounded is occurring in text; having a home is this."""
    out = set()
    for rel in documents():
        out.add(norm(rel))
        out.add(norm(Path(rel).stem))
        for line in (ROOT / rel).read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("#"):
                out.add(norm(line.lstrip("# ").strip()))
            elif line.startswith("- ["):
                out.add(norm(re.sub(r"^- \[([^\]]*)\].*", r"\1", line)))
    return out


def has_home(name: str, heads: set[str]) -> bool:
    n = norm(name)
    return any(n == h or (len(n) > 3 and n in h) for h in heads)


def subjects_without_home(ents: dict[str, dict], heads: set[str], min_docs: int) -> list[tuple[int, str, str]]:
    """Item 1: `(docs, shown name, type)` for every subject-typed entity
    that at least `min_docs` documents name and nothing titles, most
    cited first.  A subject in twenty documents with no name in the tree
    is `card:GraphRAG.md`'s *rule stated twice* at the level of subjects."""
    out = []
    for k, m in ents.items():
        if len(m["docs"]) < min_docs or not m["types"]:
            continue
        t = m["types"].most_common(1)[0][0]
        if t not in SUBJECT_TYPES:
            continue
        name = m["names"].most_common(1)[0][0]
        if not has_home(name, heads):
            out.append((len(m["docs"]), name, t))
    return sorted(out, key=lambda r: (-r[0], r[1]))


#: A number with a unit.  Bare counts — *2 questions*, *the 4 hard
#: things* — disagree everywhere and mean nothing; a number of lines,
#: seconds, tokens or per cent quoted about one subject in two documents
#: is a claim, and two claims that differ are the list.
UNIT_NUMBER = re.compile(
    r"(?<![\w./-])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*"
    r"(%|k|M|s|ms|min|MB|kB|GB|lines?|days?|hours?|minutes?|seconds?|tokens?|chunks?|files?|cards?|tests?|entries|documents?|defects?|hooks?|places?)"
    r"(?![\w-])", re.I)


def unit_numbers(text: str) -> set[tuple[str, str]]:
    return {(n.replace(",", ""), u.lower().rstrip("s")) for n, u in UNIT_NUMBER.findall(text)}


def disagreements(ents: dict[str, dict]) -> list[tuple[int, str, str, dict[str, set[str]]]]:
    """Item 2: `(docs, shown name, unit, {document: values})` for every
    entity whose descriptions quote a number with the same unit in two or
    more documents and no two documents agree on it.  No model: the
    descriptions are the model's, the comparison is arithmetic."""
    out = []
    for k, m in ents.items():
        by_unit: dict[str, dict[str, set[str]]] = {}
        for f, d in m["descriptions"]:
            for n, u in unit_numbers(d):
                by_unit.setdefault(u, {}).setdefault(f, set()).add(n)
        for u, byf in by_unit.items():
            if len(byf) < 2:
                continue
            vals = [frozenset(v) for v in byf.values()]
            if any(a & b for i, a in enumerate(vals) for b in vals[i + 1:]):
                continue                                  # two documents agree: not a disagreement
            out.append((len(m["docs"]), m["names"].most_common(1)[0][0], u, byf))
    return sorted(out, key=lambda r: (-r[0], r[1], r[2]))


def doc_dates() -> dict[str, str]:
    """Each document's last commit date, one `git log` for the tree."""
    import subprocess
    log = subprocess.run(["git", "log", "--format=%as", "--name-only", "--", "."],
                         capture_output=True, text=True, cwd=ROOT).stdout
    out, cur = {}, None
    for line in log.splitlines():
        if re.fullmatch(r"\d{4}-\d\d-\d\d", line):
            cur = line
        elif line and line not in out:
            out[line] = cur
    return out


def subjects(arm: str, min_docs: int) -> int:
    store = load_store(arm)
    ents = merged(store)
    rows = subjects_without_home(ents, headings(), min_docs)
    considered = sum(1 for m in ents.values() if len(m["docs"]) >= min_docs and m["types"]
                     and m["types"].most_common(1)[0][0] in SUBJECT_TYPES)
    print(f"(store: {len(store['records'])} chunks, written {store['written']} — a model's reading, not evidence)")
    print(f"subjects: {len(rows)} of {considered} subjects in ≥{min_docs} documents have no heading, "
          f"filename or memory hook anywhere in the tree — the plan's item 1; which are real is a person's reading")
    for d, name, t in rows:
        print(f"  {d:4d} docs  {name:44s} [{t}]")
    return 0


def contradictions(arm: str, min_docs: int, top: int) -> int:
    store = load_store(arm)
    ents = merged(store)
    rows = [r for r in disagreements(ents) if r[0] >= min_docs]
    dates = doc_dates()
    print(f"(store: {len(store['records'])} chunks, written {store['written']} — a model's reading, not evidence)")
    print(f"contradictions: {len(rows)} (subject, unit) pairs where two or more documents quote a number "
          f"and none agree — the plan's item 2; newest document last, and the number is *how many real*")
    for d, name, u, byf in rows[:top]:
        print(f"\n  {d:4d} docs  {name}  [{u}]")
        for f, v in sorted(byf.items(), key=lambda kv: (dates.get(kv[0], ""), kv[0])):
            print(f"       {dates.get(f, '?'):10s}  {f:48s} {', '.join(sorted(v, key=lambda x: float(x)))}")
    if len(rows) > top:
        print(f"\n  … and {len(rows) - top} more; --top {len(rows)} for all")
    return 0


# --- the cue at the moment: the plan's item 4 --------------------------------

#: A subject worth a cue is one a few other documents name — a hub named
#: by seventy is no route anywhere, a subject named by one other is the
#: citation graph again.
CUE_MIN_DOCS, CUE_MAX_DOCS = 2, 12
#: Not an event: the model types a date as one, and a date is a route
#: to nothing (`card:online.md`'s first cue was three dates, 2026-09-12).
CUE_TYPES = tuple(t for t in SUBJECT_TYPES if t != "event")


def cite_key(path: str) -> str:
    """A store path in the form the backlinks log names a fire by: a card
    by its id, anything else by its path."""
    m = re.match(r"board/(?:done/|later/|refused/)?([\w.-]+\.md)$", path)
    return f"card:{m.group(1)}" if m and m.group(1) != "README.md" else path


def cue(rel: str, exclude: set[str], store: dict | None = None, top: int = 3, per: int = 2) -> tuple[str, list[str]]:
    """The cue at the moment — `card:graphrag-c.md`'s item 4, decided
    2026-09-12.  For the file just read: the subjects it names that a
    few *other* documents also name, and for each, documents the reader
    had no other route to — `exclude` is what backlinks already showed,
    in citation-key form.  Deterministic, from the store, no model;
    `(line, offered keys)`, both empty when there is nothing to say.  The
    measure is the hook's own: a later fire on an offered key."""
    if store is None:
        sp = cache_dir() / "extract-haiku.json"
        if not sp.exists():
            return "", []
        store = json.loads(sp.read_text(encoding="utf-8"))
    rel = str(path_of(rel).relative_to(ROOT)) if rel.startswith("card:") else rel
    named_here: Counter = Counter()
    types: dict[str, str] = {}
    docs: dict[str, set[str]] = {}
    for rec in store["records"]:
        for e in rec["entities"]:
            k = e["norm"]
            docs.setdefault(k, set()).add(rec["file"])
            if rec["file"] == rel:
                named_here[k] += 1
                types.setdefault(k, e.get("type") or "")
    if not named_here:
        return "", []
    exclude = set(exclude) | {cite_key(rel), rel}
    parts, offered = [], []
    #: The most specific first — the subject the fewest other documents
    #: share — then the one this file names most; a generic word named
    #: everywhere ranks last, and a hub is out by the bound below.
    ranked = sorted(named_here, key=lambda k: (len(docs[k]), -named_here[k], k))
    for k in ranked:
        if types.get(k) not in CUE_TYPES or re.search(r"[_./()]", k):
            continue                    # a code identifier typed as a concept: code is not what this graph is over
        others = sorted(d for d in docs[k] if d != rel)
        if not CUE_MIN_DOCS <= len(others) <= CUE_MAX_DOCS:
            continue
        routes = [cite_key(d) for d in others if cite_key(d) not in exclude and d not in exclude][:per]
        if not routes:
            continue
        parts.append(f"*{k}* with {', '.join(routes)}")
        offered += routes
        if len(parts) >= top:
            break
    if not parts:
        return "", []
    return ("graph: this file shares " + "; ".join(parts)
            + "  (a model's reading, not evidence — python tools/graphrag.py lookup <subject>)"), offered


# --- the query: LightRAG's dual-level retrieval, one hop, one answer ------

KEYWORDS_SYSTEM = """You turn a question about a software project's repository into search keywords for a knowledge graph.
Return ONLY a JSON object: {"low": ["..."], "high": ["..."]}.
- "low": the specific things the question names or clearly refers to — files, people, tools, rules, defect numbers, named concepts — as they would be written in the repository.  Up to 8.
- "high": the themes the question is about, as one-to-three-word phrases a relation between two things might be tagged with — "working method", "authorship", "prior art".  Up to 8.
"""

KEYWORD_MODES = ("bare", "vocab")
VOCAB_ENTITIES, VOCAB_TAGS = 150, 100


def vocabulary(ents: dict[str, dict], n_entities: int = VOCAB_ENTITIES, n_tags: int = VOCAB_TAGS) -> tuple[list[str], list[str]]:
    """The tree's own words, from the store: the entity names the most
    documents name (dates left out) and the relation keywords the most
    relations carry.  Deterministic; `doc/trial/graphrag-keywords.md`."""
    names = []
    for k, m in sorted(ents.items(), key=lambda kv: (-len(kv[1]["docs"]), kv[0])):
        name = m["names"].most_common(1)[0][0]
        if re.fullmatch(r"\d{4}-\d\d-\d\d", name.strip()):
            continue
        names.append(name)
        if len(names) >= n_entities:
            break
    tags: Counter = Counter()
    seen = set()
    for m in ents.values():
        for f, other, d, st, kw in m["relations"]:
            sig = (f, d)
            if sig in seen:
                continue
            seen.add(sig)
            for t in kw:
                tags[t.lower()] += 1
    return names, [t for t, _n in tags.most_common(n_tags)]


def keywords_system(vocab: tuple[list[str], list[str]] | None) -> str:
    if not vocab:
        return KEYWORDS_SYSTEM
    names, tags = vocab
    return (KEYWORDS_SYSTEM
            + "\nThe repository calls things by its own names.  Prefer these where one fits the question, and use your own words only where none does.\n"
            + "Entity names, most-cited first: " + "; ".join(names) + "\n"
            + "Relation tags, most-used first: " + "; ".join(tags) + "\n")


ANSWER_SYSTEM = """You answer a question about a software project's repository from a CONTEXT that is a model's extraction of its documents: entities with descriptions, and relations between them, each tagged with the document it came from.
Rules:
- Answer only from the context.  Where the context does not carry what the question needs, say so in one sentence rather than filling in.
- Every claim cites the document it rests on, as the document's path in backticks, e.g. `doc/method.md` or `card:online.md`.  A sentence with no citation is a sentence the reader will discard.
- The context is testimony about the documents, not the documents; where two descriptions disagree, say both and cite both.
- 300 to 700 words, plain prose, headings allowed.
"""

STOP = set("a an the of in on at to for and or is are was were be by with from as it its this that these those which what who how does do did not no into over under about".split())


def tokens_of(text: str) -> set[str]:
    return {w.rstrip("s") for w in re.findall(r"[a-z0-9][\w./-]*", text.lower()) if w not in STOP and len(w) > 2}


RANKINGS = ("docs", "split", "themes-entities", "themes")
HOPS = ("all", "subjects")


def retrieve(ents: dict[str, dict], low: list[str], high: list[str], budget_chars: int = 40_000,
             ranking: str = "docs", hop_from: str = "all") -> dict:
    """The dual-level match, no model.  Low keywords to entity names (normalised,
    exact first, then containment); high keywords to the keywords on relations by
    shared token; then one hop from every matched entity.  Returns the context text
    and the counts.  Entities are ranked by how many documents name them,
    relations by strength, and the context is cut at `budget_chars`.

    `ranking="docs"` is the first trial's: one list, entities by document
    count, relations after — which on 2026-09-12 meant no relation ever
    reached the answer (`doc/trial/graphrag-ranking.md`).  `"split"`
    halves the budget between the two sections and orders entities by
    how they were reached — named by a low keyword, then reached by a
    high keyword's relation, then by one hop — and relations by how many
    of the question's theme tokens they carry, then strength.

    `"themes-entities"` is `split` with an entity reached by theme ranked
    by how many of its relations carry the question's tags; `"themes"`
    is that and a relation ranked by the rarity of the tags it shares,
    the sum of log(rows / rows carrying the token) over shared tokens
    (`doc/trial/graphrag-themes.md`, 2026-09-12).

    `hop_from="subjects"` keeps a document-type entity matched by a low
    keyword from hopping — it contributes itself and its descriptions,
    not its neighbourhood, because the most-cited documents are hubs
    (`doc/trial/graphrag-hubs.md`, 2026-09-12)."""
    hit_ents: dict[str, str] = {}                                   # key -> why
    for kw in low:
        k = norm(kw)
        if not k:
            continue
        if k in ents:
            hit_ents.setdefault(k, f"low:{kw}")
            continue
        for cand in sorted((c for c in ents if len(k) > 3 and (k in c or c in k)), key=lambda c: -len(ents[c]["docs"]))[:3]:
            hit_ents.setdefault(cand, f"low:{kw}")
    high_tokens = set().union(*(tokens_of(h) for h in high)) if high else set()
    hit_rels: list[tuple[int, str, str, str, str, float]] = []      # (strength, file, a, b, desc, theme score)
    seen_rel = set()
    evidence: Counter = Counter()                                    # entity -> relations of its carrying a theme tag
    #: Tag rarity over the store's relations, each counted once, for the
    #: `themes` ranking: a token on 900 rows is worth little.
    df: Counter = Counter()
    n_rows = 0
    if ranking == "themes":
        seen_df = set()
        for m in ents.values():
            for f, other, d, st, kw in m["relations"]:
                if (f, d) in seen_df:
                    continue
                seen_df.add((f, d))
                n_rows += 1
                for t in set().union(*(tokens_of(x) for x in kw)) if kw else ():
                    df[t] += 1
    import math
    for key, m in ents.items():
        for f, other, d, st, kw in m["relations"]:
            shared = high_tokens & set().union(*(tokens_of(x) for x in kw)) if kw else set()
            if not shared:
                continue
            #: Both ends of a matched relation are matched entities — the
            #: first trial marked only the end it was seen from and the
            #: other never got its hop (found by a test, 2026-09-12).
            score = (sum(math.log(n_rows / df[t]) for t in shared if df[t]) if ranking == "themes" else float(len(shared)))
            hit_ents.setdefault(key, f"high:{','.join(kw)}")
            #: An entity's evidence is its own relations' theme scores —
            #: a count under `themes-entities`, rarity-weighted under
            #: `themes` — counted from its own list only, so each row
            #: counts once per endpoint.
            evidence[key] += score
            if other in ents:
                hit_ents.setdefault(other, f"high:{','.join(kw)}")
            #: One row per (file, pair, description): the same pair in
            #: the same file may be related twice for two reasons, and
            #: keying without the description kept one (2026-09-12).
            sig = (f, min(key, other), max(key, other), d)
            if sig in seen_rel:
                continue
            seen_rel.add(sig)
            hit_rels.append((int(st or 0), f, key, other, d, score))
    hit_rels.sort(key=lambda r: -r[0])
    hop: dict[str, str] = {}
    for key in list(hit_ents):
        if (hop_from == "subjects" and hit_ents[key].startswith("low:") and ents[key]["types"]
                and ents[key]["types"].most_common(1)[0][0] == "document"):
            continue
        for f, other, d, st, kw in sorted(ents[key]["relations"], key=lambda r: -(r[3] or 0))[:12]:
            if other in ents and other not in hit_ents:
                hop.setdefault(other, f"hop:{key}")
            sig = (f, min(key, other), max(key, other), d)
            if sig not in seen_rel:
                seen_rel.add(sig)
                hit_rels.append((int(st or 0), f, key, other, d, 0))
    if ranking in ("split", "themes-entities", "themes"):
        group = {k: (0 if why.startswith("low:") else 1) for k, why in hit_ents.items()}
        group.update({k: 2 for k in hop})
        if ranking == "split":
            ranked = sorted(list(hit_ents) + list(hop), key=lambda k: (group[k], -len(ents[k]["docs"]), k))
        else:
            ranked = sorted(list(hit_ents) + list(hop), key=lambda k: (group[k], -evidence[k], -len(ents[k]["docs"]), k))
        hit_rels.sort(key=lambda r: (-r[5], -r[0]))
    else:
        ranked = sorted(list(hit_ents) + list(hop), key=lambda k: -len(ents[k]["docs"]))
        hit_rels.sort(key=lambda r: -r[0])
    ent_lines = ["## Entities"]
    for key in ranked:
        m = ents[key]
        name = m["names"].most_common(1)[0][0]
        t = m["types"].most_common(1)[0][0] if m["types"] else "?"
        ent_lines.append(f"- **{name}** [{t}] — in {len(m['docs'])} documents")
        for f, d in m["descriptions"][:3]:
            ent_lines.append(f"    - {d.strip()}  (`{f}`)")
    rel_lines = ["## Relations"]
    for st, f, a, b, d, _shared in hit_rels:
        na = ents[a]["names"].most_common(1)[0][0] if a in ents else a
        nb = ents[b]["names"].most_common(1)[0][0] if b in ents else b
        rel_lines.append(f"- {na} → {nb} ({st}): {d.strip()}  (`{f}`)")
    ent_text, rel_text = "\n".join(ent_lines), "\n".join(rel_lines)
    if ranking in ("split", "themes-entities", "themes"):
        half = budget_chars // 2
        #: Each section gets half, and what one does not use the other may.
        e_take = min(len(ent_text), max(half, budget_chars - len(rel_text)))
        r_take = min(len(rel_text), budget_chars - e_take)
        text = ent_text[:e_take] + "\n\n" + rel_text[:r_take]
        cut = len(ent_text) > e_take or len(rel_text) > r_take
    else:
        full = ent_text + "\n\n" + rel_text
        text, cut = full[:budget_chars], len(full) > budget_chars
    return {"context": text, "entities": len(hit_ents), "hop": len(hop),
            "relations": len(hit_rels), "cut": cut, "matched": hit_ents,
            "relations_in_context": text.count("\n- ") - text[:text.find("## Relations")].count("\n- ") if "## Relations" in text else 0}


def card_ids(text: str) -> str:
    """A card cited by its shelf path becomes its id — the tree's own rule
    (`board/README.md` §"How a card is cited"), which `test_citations.py`
    refused on the first trial answer (2026-09-12): the store carries
    shelf paths, and the answer copied one."""
    return re.sub(r"`board/(?:done/|later/|refused/)?([\w.-]+\.md)`",
                  lambda m: "`card:%s`" % m.group(1) if m.group(1) != "README.md" else m.group(0), text)


def cited_paths(answer: str) -> tuple[list[str], list[str]]:
    """`(resolving, not resolving)` — every backticked path or card id in
    the answer, checked against the tree.  The mechanical judge."""
    ok, bad = [], []
    for c in dict.fromkeys(re.findall(r"`([^`\n]+)`", answer)):
        c = c.strip()
        if c.startswith("card:"):
            hit = any((ROOT / shelf / c[5:]).exists() for shelf in SHELVES)
        else:
            hit = "/" in c or c.endswith(".md") or c.endswith(".py")
            hit = hit and (ROOT / c.split("#")[0].split("§")[0].strip()).exists()
        if hit:
            ok.append(c)
        elif c.endswith(".md") or c.startswith("card:") or "/" in c:
            bad.append(c)
    return ok, bad


def uncited_sentences(answer: str) -> int:
    """Sentences of the answer with no backticked citation — headings,
    the closing line and fragments under six words not counted.  The
    sheet's *a claim with no citation is counted too*."""
    n = 0
    for para in answer.split("\n"):
        para = para.strip()
        if not para or para.startswith("#") or para.startswith("*") or para.startswith("---"):
            continue
        for sent in re.split(r"(?<=[.!?])\s+", para):
            if len(sent.split()) >= 6 and "`" not in sent:
                n += 1
    return n


def query(question: str, arm: str, keywords_arm: str, answer_arm: str, backend: str, budget_chars: int,
          ranking: str = "docs", keywords: str = "bare", hop_from: str = "all") -> int:
    """The global question: keywords, retrieve, answer, count the citations.
    Prints; never writes into the tree — a person redirects it if a trial
    wants the artefact."""
    store = load_store(arm)
    ents = merged(store)
    vocab = vocabulary(ents) if keywords == "vocab" else None
    r1 = call(keywords_arm, question, max_tokens=1024, backend=backend, system=keywords_system(vocab))
    kw = parse(r1["text"])
    low = [str(x) for x in kw.get("low", []) if str(x).strip()]
    high = [str(x) for x in kw.get("high", []) if str(x).strip()]
    ret = retrieve(ents, low, high, budget_chars, ranking, hop_from)
    prompt = f"QUESTION: {question}\n\nCONTEXT:\n{ret['context']}"
    r2 = call(answer_arm, prompt, max_tokens=4096, backend=backend, system=ANSWER_SYSTEM, expect_json=False)
    answer = card_ids(r2["text"].strip())
    ok, bad = cited_paths(answer)
    spent = cost(keywords_arm, r1["usage"]) + cost(answer_arm, r2["usage"])
    print("*This is a model's reading of a model's extraction of the tree — testimony, not evidence.  "
          "`card:graphrag-c.md`.*\n")
    print(f"**Question:** {question}\n")
    tagged = f"; {sum(1 for h in high if h.lower() in set(vocab[1]))} of {len(high)} high keywords are tags in the store" if vocab else ""
    print(f"*keywords ({MODELS[keywords_arm]}, {keywords}): low {low}; high {high}{tagged}*  ")
    print(f"*retrieved: {ret['entities']} entities matched + {ret['hop']} by one hop, {ret['relations']} relations "
          f"({ret['relations_in_context']} in the context); ranking {ranking}, hop from {hop_from}; "
          f"{len(ret['context'])} chars{' (cut)' if ret['cut'] else ''}; answer by {MODELS[answer_arm]}; "
          f"{r1['usage'].get('input_tokens', 0) + r2['usage'].get('input_tokens', 0)} in, "
          f"{r1['usage'].get('output_tokens', 0) + r2['usage'].get('output_tokens', 0)} out, "
          + (f"${spent:.3f} at assumed prices" if backend == "api" else "billed to the subscription") + "*\n")
    print(answer)
    print(f"\n---\n*citations: {len(ok)} resolve, {len(bad)} do not"
          + (f" — {', '.join(bad)}" if bad else "")
          + f"; {uncited_sentences(answer)} sentence(s) with no citation*")
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


def freshness(arm: str = "haiku") -> tuple[int, int]:
    """`(chunks the tree has now, of them already extracted)` — what a
    run would have to call, without calling anything."""
    js = jobs()
    have = sum(1 for rel, i, n, text in js if cache_path_for(arm, _prompt(rel, i, n, text)).exists())
    return len(js), have


def check(arm: str = "haiku") -> int:
    import backlinks
    tree = backlinks.Tree(ROOT)
    bad = intruders(backlinks.index(tree))
    total, have = freshness(arm)
    print(f"graphrag: {have} of {total} chunks extracted ({arm}); "
          f"{total - have} would be called by `extract`"
          + (" — the graph is current" if have == total else ""))
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
    sub.add_parser("stop", help="ask a running extract to finish in-flight calls and exit")
    c = sub.add_parser("check", help="the door rule, and how much of the tree the graph has")
    c.add_argument("--arm", default="haiku", choices=list(MODELS))
    e = sub.add_parser("extract", help="every document, chunked, one call per chunk, cached")
    e.add_argument("--dry-run", action="store_true")
    e.add_argument("--arm", default="haiku", choices=list(MODELS))
    e.add_argument("--backend", choices=BACKENDS, default="cli")
    e.add_argument("--workers", type=int, default=4)
    e.add_argument("--limit", type=int, help="only the first N chunks")
    e.add_argument("--budget", type=float, help="USD at the assumed prices; the run stops when fresh api calls reach it")
    l = sub.add_parser("lookup", help="one entity across every document — the local read, no model")
    l.add_argument("name")
    l.add_argument("--arm", default="haiku", choices=list(MODELS))
    l.add_argument("--limit", type=int, default=3)
    t = sub.add_parser("entities", help="the entities most documents name")
    t.add_argument("--arm", default="haiku", choices=list(MODELS))
    t.add_argument("--top", type=int, default=30)
    t.add_argument("--type", choices=TYPES, help="only entities whose commonest type is this")
    sj = sub.add_parser("subjects", help="item 1: well-cited subjects that nothing in the tree titles — no model")
    sj.add_argument("--arm", default="haiku", choices=list(MODELS))
    sj.add_argument("--min-docs", type=int, default=6)
    cd = sub.add_parser("contradictions", help="item 2: one subject, numbers that disagree across documents — no model")
    cd.add_argument("--arm", default="haiku", choices=list(MODELS))
    cd.add_argument("--min-docs", type=int, default=2)
    cd.add_argument("--top", type=int, default=40)
    cu = sub.add_parser("cue", help="item 4: the line the backlinks hook adds for a file, from the store — no model")
    cu.add_argument("path")
    q = sub.add_parser("query", help="a global question to the graph: keywords, two-level match, one hop, one answer")
    q.add_argument("question")
    q.add_argument("--arm", default="haiku", choices=list(MODELS), help="whose extraction")
    q.add_argument("--keywords-arm", default="haiku", choices=list(MODELS))
    q.add_argument("--answer-arm", default="sonnet", choices=list(MODELS))
    q.add_argument("--backend", choices=BACKENDS, default="cli",
                   help="cli by default — Henri, 2026-09-12: the api was for bootstrapping; a cached reply is found either way")
    q.add_argument("--budget-chars", type=int, default=40_000, help="context size handed to the answer call")
    q.add_argument("--keywords", choices=KEYWORD_MODES, default="bare",
                   help="bare: the question alone; vocab: the store's entity names and relation tags in the prompt — doc/trial/graphrag-keywords.md")
    q.add_argument("--hop-from", choices=HOPS, default="all",
                   help="all: every matched entity hops; subjects: a document matched by a low keyword does not — doc/trial/graphrag-hubs.md")
    q.add_argument("--ranking", choices=RANKINGS, default="docs",
                   help="docs: the first trial's, one list by document count; split: half the budget to relations, matched entities first (doc/trial/graphrag-ranking.md); "
                        "themes-entities: split with theme-reached entities ranked by their tagged relations; themes: that and relations by tag rarity (doc/trial/graphrag-themes.md)")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        return check(a.arm)
    if a.cmd == "stop":
        (cache_dir() / "extract.stop").touch()
        pid = (cache_dir() / "extract.pid").read_text().split()[-1] if (cache_dir() / "extract.pid").exists() else "?"
        print(f"graphrag: stop asked; the run (pid {pid}) finishes its calls in flight and exits")
        return 0
    if a.cmd == "lookup":
        return lookup(a.name, a.arm, a.limit)
    if a.cmd == "entities":
        return entities_top(a.arm, a.top, a.type)
    if a.cmd == "subjects":
        return subjects(a.arm, a.min_docs)
    if a.cmd == "contradictions":
        return contradictions(a.arm, a.min_docs, a.top)
    if a.cmd == "cue":
        line, offered = cue(a.path, set())
        print(line or f"cue: nothing to say about {a.path}")
        return 0
    if a.cmd == "query":
        return query(a.question, a.arm, a.keywords_arm, a.answer_arm, a.backend, a.budget_chars, a.ranking, a.keywords, a.hop_from)
    if a.cmd == "extract":
        return extract(a.arm, a.backend, a.workers, a.limit, a.dry_run, a.budget)
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]
    for x in arms:
        if x not in MODELS:
            sys.exit(f"graphrag: unknown arm `{x}`; known: {', '.join(MODELS)}")
    return pilot(a.dry_run, arms, Path(a.out), a.backend, a.files)


if __name__ == "__main__":
    sys.exit(main())
