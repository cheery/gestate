"""`tools/graphrag.py` — the door, and the mechanics the pilot scores with.

`card:graphrag-c.md`: the subject graph under `doc/graph/` is a model's
reading of the tree and is not evidence, so **nothing outside that
directory may cite a file inside it other than its README**.  The first
test is that rule over the real tree; the second is the rule on a made-up
index, so the checker has been seen to fail before it is trusted.
Nothing here makes an API call.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import backlinks  # noqa: E402
import graphrag  # noqa: E402


def test_nothing_outside_the_graph_cites_into_it():
    tree = backlinks.Tree(ROOT)
    assert graphrag.intruders(backlinks.index(tree)) == [], (
        "a file outside doc/graph/ cites a generated page — card:graphrag-c.md says why not")


def test_the_door_check_sees_an_intruder_and_lets_the_readme_through():
    index = {
        "doc/memory/x.md": {"c": [[3, "doc/graph/community-7.md", "…", False]]},
        "spec/y.md": {"c": [[9, "doc/graph/README.md", "…", False]]},
        "doc/graph/community-7.md": {"c": [[1, "doc/graph/community-8.md", "…", False]]},
    }
    assert graphrag.intruders(index) == [("doc/memory/x.md", 3, "doc/graph/community-7.md")]


def test_grounded_is_the_text_and_not_the_model():
    text = "The andon — `tools/andon.sh` — rings the sound card; F169 is the number rule."
    assert graphrag.grounded("tools/andon.sh", text)
    assert graphrag.grounded("`tools/andon.sh`", text)
    assert graphrag.grounded("the andon", text)
    assert graphrag.grounded("F169", text)
    assert graphrag.grounded("sound card rings", text)          # every word present
    assert not graphrag.grounded("Toyota Production System", text)
    assert not graphrag.grounded("Henri", text)


def test_parse_takes_the_object_out_of_prose_and_survives_junk():
    good = 'Here it is:\n{"entities": [{"name": "F1", "type": "defect", "description": "d"}], "relations": []}\nDone.'
    assert graphrag.parse(good)["entities"][0]["name"] == "F1"
    bad = graphrag.parse("no json at all")
    assert bad["entities"] == [] and bad["parse_error"]
    broken = graphrag.parse('{"entities": [')
    assert broken["entities"] == [] and broken["parse_error"]


def test_the_pilot_files_exist_and_fit():
    for rel in graphrag.PILOT:
        p = graphrag.path_of(rel)
        assert p.exists(), rel
        assert len(p.read_text(encoding="utf-8")) <= graphrag.MAX_CHARS, f"{rel} would be truncated"


def test_a_relation_keeps_its_keywords_whatever_shape_the_model_gave():
    """2026-09-12: the prompt asks for `keywords` on a relation, the field
    LightRAG's high-level retrieval matches; the store normalises it."""
    assert "keywords" in graphrag.SYSTEM
    assert graphrag.relation({"source": "a", "target": "b", "keywords": ["testing standard", " ", "commit rights"]})["keywords"] == ["testing standard", "commit rights"]
    assert graphrag.relation({"source": "a", "target": "b", "keywords": "audio teardown, sound card"})["keywords"] == ["audio teardown", "sound card"]
    assert graphrag.relation({"source": "a", "target": "b"})["keywords"] == []
    assert graphrag.relation({"source": "a", "target": "b", "keywords": 7})["keywords"] == []


def test_a_store_from_another_prompt_is_set_aside_and_not_carried(tmp_path):
    """A record extracted under an older prompt lacks what the prompt now
    asks for; the run starts its store over and keeps the old file."""
    import json
    sp = tmp_path / "extract-haiku.json"
    rec = {"id": "x.md#0", "usage": {"output_tokens": 5}, "entities": [], "relations": []}
    hole = {"id": "y.md#0", "usage": {"output_tokens": 0}, "entities": [], "relations": []}
    sp.write_text(json.dumps({"prompt": "2000-01-01a", "records": [rec]}), encoding="utf-8")
    assert graphrag.seed_records(sp) == {}
    assert not sp.exists() and (tmp_path / "extract-haiku.2000-01-01a.json").exists()
    sp.write_text(json.dumps({"prompt": graphrag.PROMPT_VERSION, "records": [rec, hole]}), encoding="utf-8")
    assert list(graphrag.seed_records(sp)) == ["x.md#0"]
    assert graphrag.seed_records(tmp_path / "none.json") == {}


def test_the_cache_does_not_know_the_backend():
    """2026-09-12, Henri: the first run on the api, the increments on the
    cli — so a reply is keyed without the backend and found by either."""
    import inspect
    assert "backend" not in inspect.signature(graphrag.cache_path_for).parameters
    a = graphrag.cache_path_for("haiku", "Document `x.md`:\n\nsome text")
    assert a == graphrag.cache_path_for("haiku", "Document `x.md`:\n\nsome text")
    assert a != graphrag.cache_path_for("sonnet", "Document `x.md`:\n\nsome text")
    assert a != graphrag.cache_path_for("haiku", "Document `x.md`:\n\nother text")
    assert a.parent.name == "haiku" and a.parent.parent == graphrag.cache_dir()


def test_pagerank_ranks_the_hub_first_and_the_isolate_last():
    star = {"hub": {"a": 1.0, "b": 1.0, "c": 1.0}, "a": {"hub": 1.0}, "b": {"hub": 1.0}, "c": {"hub": 1.0}, "lone": {}}
    pr = graphrag.pagerank(star)
    assert pr["hub"] > pr["a"] == pr["b"] == pr["c"] > pr["lone"] > 0
    assert abs(sum(pr.values()) - 1.0) < 1e-6
    assert graphrag.pagerank({}) == {}


def test_extraction_jobs_run_the_central_documents_first():
    """A budget stop leaves out the periphery, not the end of the alphabet."""
    js = graphrag.jobs()
    order = []
    for rel, _i, _n, _t in js:
        if rel not in order:
            order.append(rel)
    pr = graphrag.centrality()
    assert pr.get(order[0], 0) > pr.get(order[-1], 0)
    assert order[0] != sorted(order)[0] or pr.get(order[0], 0) >= max(pr.get(r, 0) for r in order)
    ranks = [pr.get(r, 0.0) for r in order]
    assert ranks == sorted(ranks, reverse=True)
