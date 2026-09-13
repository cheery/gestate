#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-11 — "tee se tutkimus nyt, kortti day one" — card:GraphRAG.md
"""Does the tree's hand-drawn map match where its citations cluster?

    python tools/communities.py                 the measurement, as the sheet says
    python tools/communities.py --written-only  robustness: written citations, no mentions
    python tools/communities.py --edges out.tsv also write the edge list, re-runnable without the tree
    python tools/communities.py --selftest      the algorithm on graphs whose answer is known

`card:GraphRAG.md`, day one, steps 2 and 3.  The sheet is
`doc/trial/graphrag.md`; nothing here decides, it prints.

**The graph is the tree's own** — every citation `tools/backlinks.py`
already indexes: `file.md §"…"`, `card:<name>.md`, `[[memory]]`, an
F-number, and a file named in passing.  One node per file; a card, a
memory or a defect resolves to the file that carries it (the card's
Q2 default).  Undirected, unweighted.

**The partition is computed, not written.**  Louvain modularity
optimisation in pure Python, seeded, because no graph library is in
the checkout and the graph is a few hundred nodes.  Not Leiden: Leiden
guarantees each community is connected and Louvain does not, which is
named in the output so a later Leiden run on the same edge list can be
compared.

**The hand-drawn map is two things**: the top-level directory of each
file, the board's shelves as one; and, for `gestate/*.py`, the lane
`gestate/atlas.py` places each module in.  Agreement is normalised
mutual information (NMI, natural log, arithmetic mean normalisation)
and the adjusted Rand index; the null is a degree-preserving rewiring
of the same graph.

**What the output is for is the disagreement list**, not the score —
`card:GraphRAG.md` §"Found by looking": a computed community that
straddles two directories is a subject the tree has not named; a
memory alone in its community is an orphan or the one place a rule
lives; two memories alone together are a *rule stated twice*
candidate.  Each is a lamp for a person, never a gate.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import backlinks  # noqa: E402

Adj = dict[str, dict[str, float]]


# --- the graph ---------------------------------------------------------------

def resolve(tree: backlinks.Tree, key: str) -> str | None:
    """A backlinks index key to the file that carries it."""
    if key.startswith("card:"):
        for shelf in backlinks.SHELVES:
            rel = f"{shelf}/{key[5:]}"
            if rel in tree.rel:
                return rel
        return None
    if key.startswith("mem:"):
        rel = f"doc/memory/{key[4:]}.md"
        return rel if rel in tree.rel else None
    if key.startswith("F") and key[1:].isdigit():
        rel = f"fixme/{key}.md"                 # one file an entry since 2026-09-13
        return rel if rel in tree.rel else "fixme.md"
    return key if key in tree.rel else None


def graph(tree: backlinks.Tree, written_only: bool = False) -> tuple[Adj, int]:
    """Undirected, unweighted; `(adjacency, citations read)`."""
    adj: Adj = defaultdict(dict)
    read = 0
    for rel, entry in backlinks.index(tree).items():
        for _line, key, _text, explicit in entry["c"]:
            if written_only and not explicit:
                continue
            target = resolve(tree, key)
            read += 1
            if target is None or target == rel:
                continue
            adj[rel][target] = 1.0
            adj[target][rel] = 1.0
    return {n: dict(nb) for n, nb in adj.items()}, read


def edge_list(adj: Adj) -> list[tuple[str, str]]:
    return sorted({tuple(sorted((a, b))) for a in adj for b in adj[a]})


# --- Louvain -----------------------------------------------------------------

def modularity(adj: Adj, part: dict[str, int]) -> float:
    m2 = sum(w for nb in adj.values() for w in nb.values())  # 2m
    if m2 == 0:
        return 0.0
    k = {n: sum(nb.values()) for n, nb in adj.items()}
    q = 0.0
    for a, nb in adj.items():
        for b, w in nb.items():
            if part[a] == part[b]:
                q += w - k[a] * k[b] / m2
    return q / m2


def _one_level(adj: Adj, rng: random.Random) -> tuple[dict[str, int], bool]:
    """Local moving until no node improves modularity.  Returns the
    partition and whether anything moved."""
    m2 = sum(w for nb in adj.values() for w in nb.values())
    k = {n: sum(nb.values()) for n, nb in adj.items()}
    part = {n: i for i, n in enumerate(adj)}
    tot = {part[n]: k[n] for n in adj}                # sum of degrees per community
    moved_any = False
    nodes = list(adj)
    while True:
        rng.shuffle(nodes)
        moved = False
        for n in nodes:
            c_old = part[n]
            links = defaultdict(float)                  # weight from n into each community
            for b, w in adj[n].items():
                links[part[b]] += w
            tot[c_old] -= k[n]
            best, best_gain = c_old, links[c_old] - tot[c_old] * k[n] / m2
            for c, w in links.items():
                gain = w - tot[c] * k[n] / m2
                if gain > best_gain + 1e-12 or (abs(gain - best_gain) <= 1e-12 and c < best):
                    best, best_gain = c, gain
            tot[best] += k[n]
            if best != c_old:
                part[n] = best
                moved = moved_any = True
        if not moved:
            break
    return part, moved_any


def _aggregate(adj: Adj, part: dict[str, int]) -> Adj:
    out: Adj = defaultdict(lambda: defaultdict(float))
    for a, nb in adj.items():
        for b, w in nb.items():
            out[str(part[a])][str(part[b])] += w
    return {n: dict(nb) for n, nb in out.items()}


def louvain(adj: Adj, seed: int = 0) -> dict[str, int]:
    """Multi-level Louvain.  Deterministic for a seed."""
    rng = random.Random(seed)
    membership = {n: n for n in adj}                    # node → current super-node
    level = adj
    while True:
        part, moved = _one_level(level, rng)
        if not moved:
            break
        membership = {n: str(part[membership[n]]) for n in membership}
        level = _aggregate(level, part)
        if len(level) == len(part) and len(set(part.values())) == len(part):
            break
    ids = {c: i for i, c in enumerate(sorted(set(membership.values()), key=str))}
    return {n: ids[c] for n, c in membership.items()}


# --- comparing partitions ----------------------------------------------------

def nmi(a: dict[str, int], b: dict[str, int]) -> float:
    nodes = [n for n in a if n in b]
    n = len(nodes)
    if n == 0:
        return 0.0
    ca, cb, cab = Counter(), Counter(), Counter()
    for x in nodes:
        ca[a[x]] += 1
        cb[b[x]] += 1
        cab[(a[x], b[x])] += 1
    ha = -sum(c / n * math.log(c / n) for c in ca.values())
    hb = -sum(c / n * math.log(c / n) for c in cb.values())
    mi = sum(c / n * math.log(c * n / (ca[i] * cb[j])) for (i, j), c in cab.items())
    denom = (ha + hb) / 2
    return mi / denom if denom > 0 else 1.0


def ari(a: dict[str, int], b: dict[str, int]) -> float:
    nodes = [n for n in a if n in b]
    ca, cb, cab = Counter(), Counter(), Counter()
    for x in nodes:
        ca[a[x]] += 1
        cb[b[x]] += 1
        cab[(a[x], b[x])] += 1

    def c2(v: int) -> float:
        return v * (v - 1) / 2

    idx = sum(c2(v) for v in cab.values())
    ea = sum(c2(v) for v in ca.values())
    eb = sum(c2(v) for v in cb.values())
    n = len(nodes)
    expected = ea * eb / c2(n) if n > 1 else 0
    maximum = (ea + eb) / 2
    return (idx - expected) / (maximum - expected) if maximum != expected else 1.0


# --- the hand-drawn maps -----------------------------------------------------

def by_directory(nodes, depth: int = 1) -> dict[str, str]:
    out = {}
    for n in nodes:
        parts = n.split("/")
        if parts[0] == "board":
            out[n] = "board"                            # the shelves as one
        elif len(parts) == 1:
            out[n] = "(root)"
        else:
            out[n] = "/".join(parts[:min(depth, len(parts) - 1)])
    return out


def by_lane(nodes) -> dict[str, str]:
    from gestate import atlas
    out = {}
    for n in nodes:
        if n.startswith("gestate/") and n.endswith(".py"):
            mod = n[len("gestate/"):-3].replace("/", ".")
            if mod in atlas.WHERE:
                out[n] = atlas.WHERE[mod]
    return out


def induced(adj: Adj, keep) -> Adj:
    keep = set(keep)
    return {a: {b: w for b, w in nb.items() if b in keep}
            for a, nb in adj.items() if a in keep}


# --- the null ----------------------------------------------------------------

def rewired(adj: Adj, seed: int) -> Adj:
    """Degree-preserving double-edge swaps, 10 per edge."""
    rng = random.Random(seed)
    edges = edge_list(adj)
    present = set(edges)
    swaps = 0
    tries = 0
    while swaps < 10 * len(edges) and tries < 100 * len(edges):
        tries += 1
        i, j = rng.randrange(len(edges)), rng.randrange(len(edges))
        (a, b), (c, d) = edges[i], edges[j]
        if rng.random() < 0.5:
            c, d = d, c
        if len({a, b, c, d}) < 4:
            continue
        e1, e2 = tuple(sorted((a, d))), tuple(sorted((c, b)))
        if e1 in present or e2 in present:
            continue
        present.discard(edges[i])
        present.discard(edges[j])
        present.add(e1)
        present.add(e2)
        edges[i], edges[j] = e1, e2
        swaps += 1
    out: Adj = defaultdict(dict)
    for a, b in edges:
        out[a][b] = 1.0
        out[b][a] = 1.0
    return {n: dict(nb) for n, nb in out.items()}


# --- the disagreement list ---------------------------------------------------

def disagreements(part: dict[str, int], hand: dict[str, str]) -> list[str]:
    groups: dict[int, list[str]] = defaultdict(list)
    for n, c in part.items():
        groups[c].append(n)
    out = []
    for c, members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        dirs = Counter(hand.get(n, "?") for n in members)
        top = dirs.most_common()
        mems = [n for n in members if n.startswith("doc/memory/")]
        if len(top) >= 2 and top[1][1] >= 3:
            spread = ", ".join(f"{d} {k}" for d, k in top[:4])
            out.append(f"straddles   community {c} ({len(members)}): {spread}"
                       + (f"; e.g. {', '.join(sorted(members)[:4])}"))
        if len(members) <= 2 and mems and len(mems) == len(members):
            kind = "orphan     " if len(members) == 1 else "twice?     "
            out.append(f"{kind} community {c}: {', '.join(sorted(members))}")
    return out


# --- self-test ---------------------------------------------------------------

def _clique(names) -> Adj:
    return {a: {b: 1.0 for b in names if b != a} for a in names}


def selftest() -> int:
    """Graphs whose communities are known.  Exit 1 on the first wrong one."""
    a = _clique([f"a{i}" for i in range(6)])
    b = _clique([f"b{i}" for i in range(6)])
    g = {**a, **b}
    g["a0"]["b0"] = 1.0
    g["b0"]["a0"] = 1.0
    part = louvain(g, seed=1)
    ok = len({part[n] for n in a}) == 1 and len({part[n] for n in b}) == 1 and part["a0"] != part["b0"]
    print("two cliques, one bridge:", "two communities" if ok else f"WRONG {part}")
    if not ok:
        return 1
    ring: Adj = {}
    cl = [[f"c{k}{i}" for i in range(5)] for k in range(3)]
    for names in cl:
        ring.update(_clique(names))
    for k in range(3):
        x, y = cl[k][0], cl[(k + 1) % 3][1]
        ring[x][y] = ring[y][x] = 1.0
    part = louvain(ring, seed=3)
    ok = len({part[n] for n in ring}) == 3 and all(len({part[n] for n in names}) == 1 for names in cl)
    print("ring of three cliques:", "three communities" if ok else f"WRONG {part}")
    if not ok:
        return 1
    full = {n: n for n in ring}
    print("nmi of a partition with itself:", round(nmi(part, part), 3), "ari:", round(ari(part, part), 3))
    print("nmi against singletons:", round(nmi(part, {n: i for i, n in enumerate(full)}), 3))
    return 0


# --- main --------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--written-only", action="store_true", help="written citations only, no file named in passing")
    ap.add_argument("--edges", help="write the edge list here (TSV)")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--nulls", type=int, default=20)
    ap.add_argument("--json", action="store_true", help="a one-line summary, for the journal")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    tree = backlinks.Tree(ROOT)
    adj, read = graph(tree, a.written_only)
    edges = edge_list(adj)
    if a.edges:
        Path(a.edges).write_text("".join(f"{x}\t{y}\n" for x, y in edges), encoding="utf-8")
    print(f"graph: {len(adj)} files with a citation, {len(edges)} edges, from {read} citations"
          f"{' (written only)' if a.written_only else ''}; "
          f"{len(tree.rel) - len(adj)} files cite nothing and are cited by nothing")

    parts = [louvain(adj, seed=s) for s in range(a.seeds)]
    q = [modularity(adj, p) for p in parts]
    stab = [nmi(parts[0], p) for p in parts[1:]]
    sizes = Counter(parts[0].values())
    print(f"louvain: seed 0 gives {len(sizes)} communities, largest {max(sizes.values())}, "
          f"modularity {q[0]:.3f} (over {a.seeds} seeds: {min(q):.3f}–{max(q):.3f}); "
          f"stability NMI vs seed 0: mean {sum(stab)/len(stab):.3f}, min {min(stab):.3f}")
    print("   (Louvain, not Leiden: a community here may be disconnected)")

    hand1 = by_directory(adj, 1)
    hand2 = by_directory(adj, 2)
    n1 = [nmi(p, hand1) for p in parts]
    r1 = [ari(p, hand1) for p in parts]
    n2 = [nmi(p, hand2) for p in parts]
    print(f"vs directories (top level, {len(set(hand1.values()))} of them): "
          f"NMI {n1[0]:.3f} (seeds {min(n1):.3f}–{max(n1):.3f}), ARI {r1[0]:.3f}")
    print(f"vs directories (two levels, {len(set(hand2.values()))} of them): "
          f"NMI {n2[0]:.3f} (seeds {min(n2):.3f}–{max(n2):.3f})   — robustness, not the decision")

    nulls = []
    for s in range(a.nulls):
        g = rewired(adj, seed=1000 + s)
        p = louvain(g, seed=s)
        nulls.append(nmi(p, by_directory(g, 1)))
    print(f"null (degree-preserving rewiring, {a.nulls} draws): NMI vs directories "
          f"mean {sum(nulls)/len(nulls):.3f}, max {max(nulls):.3f}")

    lane = by_lane(adj)
    sub = induced(adj, lane)
    sub = {n: nb for n, nb in sub.items() if nb}
    if len(sub) >= 10:
        lp = louvain(sub, seed=0)
        print(f"vs atlas lanes (gestate/*.py, {len(sub)} modules with a citation among themselves, "
              f"{len(set(lane[n] for n in sub))} lanes): NMI {nmi(lp, lane):.3f}, ARI {ari(lp, lane):.3f}")
    else:
        print(f"vs atlas lanes: only {len(sub)} modules cite each other — too sparse to compare")

    dis = disagreements(parts[0], hand1)
    print(f"\ndisagreements with the top-level directories ({len(dis)}), seed 0:")
    for line in dis:
        print("  " + line)

    if a.json:
        print(json.dumps({"files": len(adj), "edges": len(edges), "communities": len(sizes),
                          "modularity": round(q[0], 3), "nmi_dirs": round(n1[0], 3),
                          "ari_dirs": round(r1[0], 3), "nmi_dirs2": round(n2[0], 3),
                          "null_max": round(max(nulls), 3), "stability_min": round(min(stab), 3),
                          "disagreements": len(dis)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
