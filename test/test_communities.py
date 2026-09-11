"""`tools/communities.py` — the algorithm on graphs whose answer is known.

`card:GraphRAG.md`.  The tool is a lamp, not a gate: nothing here asserts
anything about the tree's partition.  What is asserted is that the
partitioner finds the communities a person can see by eye, so a number it
prints about the tree is a number and not a bug.  Broken on purpose once
on 2026-09-11 (the modularity gain's sign flipped) before it was trusted:
the two-clique graph came back as twelve singletons.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import communities  # noqa: E402


def _clique(names):
    return {a: {b: 1.0 for b in names if b != a} for a in names}


def test_two_cliques_joined_by_one_edge_are_two_communities():
    a = [f"a{i}" for i in range(6)]
    b = [f"b{i}" for i in range(6)]
    g = {**_clique(a), **_clique(b)}
    g["a0"]["b0"] = g["b0"]["a0"] = 1.0
    part = communities.louvain(g, seed=1)
    assert len({part[n] for n in a}) == 1
    assert len({part[n] for n in b}) == 1
    assert part["a0"] != part["b0"]


def test_a_ring_of_three_cliques_is_three_communities():
    cl = [[f"c{k}{i}" for i in range(5)] for k in range(3)]
    g = {}
    for names in cl:
        g.update(_clique(names))
    for k in range(3):
        x, y = cl[k][0], cl[(k + 1) % 3][1]
        g[x][y] = g[y][x] = 1.0
    part = communities.louvain(g, seed=3)
    assert len(set(part.values())) == 3
    assert all(len({part[n] for n in names}) == 1 for names in cl)


def test_nmi_and_ari_are_one_for_a_partition_against_itself_and_less_otherwise():
    part = {f"n{i}": i // 4 for i in range(12)}
    assert abs(communities.nmi(part, part) - 1.0) < 1e-9
    assert abs(communities.ari(part, part) - 1.0) < 1e-9
    singletons = {n: i for i, n in enumerate(part)}
    assert communities.nmi(part, singletons) < 1.0
    assert communities.ari(part, singletons) < 0.5


def test_rewiring_keeps_every_degree():
    cl = [[f"c{k}{i}" for i in range(5)] for k in range(3)]
    g = {}
    for names in cl:
        g.update(_clique(names))
    for k in range(3):
        x, y = cl[k][0], cl[(k + 1) % 3][1]
        g[x][y] = g[y][x] = 1.0
    h = communities.rewired(g, seed=7)
    assert {n: len(nb) for n, nb in g.items()} == {n: len(nb) for n, nb in h.items()}
    assert len(communities.edge_list(g)) == len(communities.edge_list(h))
