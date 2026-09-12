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


def test_a_reply_with_one_stray_brace_is_salvaged_object_by_object():
    """Chunk 80 of the 2026-09-12 run, in miniature: the second relation
    closes after its description; the rest is recovered, the error kept."""
    text = """```json
{"entities": [{"name": "F126", "type": "defect", "description": "a crash"},
              {"name": "vision.md", "type": "document", "description": "the vision"}],
 "relations": [{"source": "F126", "target": "vision.md", "description": "ok", "keywords": ["k"], "strength": 7},
               {"source": "doc/consent.md", "target": "Henri", "description": "broken"},
      "keywords": ["consent protocol"], "strength": 9},
               {"source": "vision.md", "target": "F126", "description": "fine", "keywords": ["x"], "strength": 6}]}
```"""
    obj = graphrag.parse(text)
    assert [e["name"] for e in obj["entities"]] == ["F126", "vision.md"]
    assert [r["description"] for r in obj["relations"]] == ["ok", "broken", "fine"]
    assert obj["parse_error"].endswith("salvaged 2 entities, 3 relations")
    assert graphrag.relation(obj["relations"][1])["keywords"] == []


def _ent(names, types, docs, descriptions):
    from collections import Counter
    return {"names": Counter(names), "types": Counter(types), "docs": set(docs),
            "descriptions": descriptions, "relations": []}


def test_subjects_without_home_is_the_well_cited_and_untitled():
    ents = {
        "toyota production system": _ent(["Toyota Production System"], ["concept"], list("abcdefg"), []),
        "andon": _ent(["andon"], ["concept"], list("abcdefg"), []),               # titled: a heading
        "rare thing": _ent(["rare thing"], ["concept"], ["a"], []),               # one document
        "fixme": _ent(["fixme.md"], ["document"], list("abcdefg"), []),           # a document has a home by construction
    }
    heads = {"the andon", "fixme", "board/readme"}
    assert graphrag.subjects_without_home(ents, heads, 6) == [(7, "Toyota Production System", "concept")]
    assert graphrag.has_home("andon", heads) and not graphrag.has_home("F169", heads)


def test_disagreements_is_units_only_and_agreement_anywhere_clears_it():
    ents = {
        "spec/rules": _ent(["spec/rules.md"], ["document"], ["j", "r", "m"], [
            ("j", "The rules, capped at 2000 lines."),
            ("r", "Five documents under a 2500 lines cap."),
        ]),
        "agreed": _ent(["agreed"], ["concept"], ["a", "b", "c"], [
            ("a", "runs in 15 s"), ("b", "about 15 s"), ("c", "30 s on a cold start"),   # a and b agree
        ]),
        "bare": _ent(["bare"], ["concept"], ["a", "b"], [
            ("a", "the 2 questions"), ("b", "the 4 questions"),                          # no unit: not a claim
        ]),
    }
    rows = graphrag.disagreements(ents)
    assert [(r[1], r[2]) for r in rows] == [("spec/rules.md", "line")]
    assert rows[0][3] == {"j": {"2000"}, "r": {"2500"}}
    assert graphrag.unit_numbers("1,554 lines and 2026-09-06 and 15 %") == {("1554", "line"), ("15", "%")}


def test_retrieve_matches_low_to_names_high_to_relation_keywords_and_hops_once():
    ents = {
        "vision": _ent(["vision.md"], ["document"], ["a", "b", "c"], [("a", "the author's own document")]),
        "henri": _ent(["Henri"], ["person"], ["a", "b"], [("b", "the keeper")]),
        "tps": _ent(["Toyota Production System"], ["concept"], ["c"], [("c", "the source")]),
        "far": _ent(["far"], ["concept"], ["d"], [("d", "unrelated")]),
    }
    ents["vision"]["relations"] = [("a", "henri", "Henri wrote vision.md", 9, ("authorship",))]
    ents["henri"]["relations"] = [("a", "vision", "Henri wrote vision.md", 9, ("authorship",)),
                                  ("c", "tps", "Henri read TPS in July", 6, ("method sources", "prior art"))]
    ents["tps"]["relations"] = [("c", "henri", "Henri read TPS in July", 6, ("method sources", "prior art"))]
    r = graphrag.retrieve(ents, low=["vision.md"], high=["prior art"])
    assert set(r["matched"]) == {"vision", "henri"}          # low by name; high by the relation's keyword
    assert r["hop"] == 1 and "Toyota Production System" in r["context"]   # one hop from henri reaches tps
    assert "unrelated" not in r["context"] and r["relations"] == 2
    assert "(`a`)" in r["context"]                            # every line carries its document


def test_cited_paths_is_the_tree_and_not_the_answer():
    ok, bad = graphrag.cited_paths("See `doc/method.md`, `card:online.md`, `doc/nothing-here.md` and `tools/graphrag.py`; also `F169`.")
    assert ok == ["doc/method.md", "card:online.md", "tools/graphrag.py"]
    assert bad == ["doc/nothing-here.md"]


def test_a_system_prompt_is_part_of_the_cache_key_and_the_default_keeps_the_old_keys():
    a = graphrag.cache_path_for("haiku", "q")
    assert a == graphrag.cache_path_for("haiku", "q", system=graphrag.SYSTEM)
    assert a != graphrag.cache_path_for("haiku", "q", system=graphrag.KEYWORDS_SYSTEM)


def test_the_graph_never_reads_its_own_answers():
    assert not [d for d in graphrag.documents() if "/graphrag-global/" in d or "/graphrag-pilot/" in d]


def test_uncited_sentences_counts_claims_and_not_headings():
    text = "## Heading\nThe keeper is Henri, see `keeper.md`. This sentence makes a claim with no citation at all.\n*a footer line*\nShort one."
    assert graphrag.uncited_sentences(text) == 1


def test_an_answer_cites_a_card_by_id_never_by_shelf():
    shelf = "board/"                                          # spelled at run time: the citation gate reads this file too
    text = f"see `{shelf}gui-is-difficult.md`, `{shelf}done/peep-window.md`, `{shelf}README.md` and `doc/method.md`"
    assert graphrag.card_ids(text) == f"see `card:gui-is-difficult.md`, `card:peep-window.md`, `{shelf}README.md` and `doc/method.md`"
