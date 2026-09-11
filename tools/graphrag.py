#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-11 — "ok. Tehdään C, ja järjestetään se siten että graafi on toistaiseksi vain itseviittaava … Ja ajetaan pilotti." — card:graphrag-c.md
"""A subject graph over the tree's documents, extracted by a model — self-referential until it earns a citer.

    python tools/graphrag.py pilot                 ten files, two models, one prompt; the sheet is doc/trial/graphrag-pilot.md
    python tools/graphrag.py pilot --dry-run       the files, the sizes and the prompt, no call made
    python tools/graphrag.py check                 the door rule: nothing outside doc/graph/ cites into it

`card:graphrag-c.md`.  What is built today is the pilot and the door;
`extract`, `communities`, `summarise` and `query` follow in that order,
each when the one before has earned it.

**Nothing this tool produces is evidence.**  An extraction is a model's
reading of a file; a summary is a model's reading of extractions.  The
door rule is what keeps that true mechanically: `test/test_graphrag.py`
refuses a commit in which any file outside `doc/graph/` cites a file
inside it other than `doc/graph/README.md`.

**The API is reached with the standard library**, `urllib`, so nothing
has to be installed: `ANTHROPIC_API_KEY` in the environment is the
whole requirement, and `tools/toolbox.sh` reports whether it is there.
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

def cache_dir() -> Path:
    home = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return home / "gestate" / "graphrag"


def call(model_key: str, text: str, max_tokens: int = MAX_TOKENS) -> dict:
    """One Messages call, cached.  Returns `{"text", "usage", "model", "stop_reason", "cached"}`."""
    model = MODELS[model_key]
    params = PARAMS.get(model_key, {})
    key = hashlib.sha1(f"{model}\n{PROMPT_VERSION}\n{max_tokens}\n{json.dumps(params, sort_keys=True)}\n{SYSTEM}\n{text}".encode()).hexdigest()
    cp = cache_dir() / model_key / f"{key}.json"
    if cp.exists():
        out = json.loads(cp.read_text(encoding="utf-8"))
        out["cached"] = True
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

def pilot(dry_run: bool, arms: list[str], out_dir: Path) -> int:
    files = []
    for rel in PILOT:
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
            r = call(arm, f"Document `{rel}`:\n\n{text}")
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
        for rel in PILOT:
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
    sub.add_parser("check", help="the door rule")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        return check()
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]
    for x in arms:
        if x not in MODELS:
            sys.exit(f"graphrag: unknown arm `{x}`; known: {', '.join(MODELS)}")
    return pilot(a.dry_run, arms, Path(a.out))


if __name__ == "__main__":
    sys.exit(main())
