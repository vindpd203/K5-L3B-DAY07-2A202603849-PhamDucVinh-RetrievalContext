"""T0.5: convert Day 6 benchmark (jsonl) to Day 7 schema -> data/questions.json, then check evidence reachability.

Hit rule = Day 6 `is_evidence_hit` (reused in later eval): same source, gold page in the chunk's pages, and the
whole evidence is a substring of the chunk after collapsing whitespace (OCR breaks lines mid-sentence).
Questions whose evidence no chunk contains stay in the benchmark (real chunking misses) and are only reported.
Do NOT use starter/baseline.py validate()/hit(): they compare without collapsing whitespace.
"""
import json
from pathlib import Path

SRC = Path("../../Day6/K5-L3B-Day06-DataIngestionEngineering/benchmark/questions.jsonl")


def squash(s):
    return " ".join(s.split())


def hit(chunk, gold):
    pages = chunk["metadata"].get("pages") or [chunk["page"]]
    text = squash(chunk["text"])
    return any(chunk["source_id"] == g["source_id"] and g["page"] in pages and squash(g["evidence"]) in text
               for g in gold)


def main():
    qs = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = [{"id": q["id"], "split": q["split"], "type": q["type"], "question": q["question"],
            "expected_answer": q["expected_answer"], "filter": q["filter"],
            # one alternative gold entry per page, page as int
            "gold": [{"source_id": q["gold_source_id"], "page": int(p), "evidence": q["evidence_quote"]}
                     for p in q["gold_page"]],
            # human-only notes from Day 6 (never sent to the agent)
            **{k: q[k] for k in ("article", "filter_context", "note") if k in q}}
           for q in qs]
    assert len({q["id"] for q in out}) == len(out), "duplicate question id"
    Path("data/questions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n_dev = sum(q["split"] == "dev" for q in out)
    print(f"{len(out)} câu: {n_dev} dev / {len(out) - n_dev} test -> data/questions.json")

    for s in ("A", "B"):
        chunks = json.loads(Path(f"data/chunks_{s}.json").read_text(encoding="utf-8"))
        miss = [q["id"] for q in out if not any(hit(c, q["gold"]) for c in chunks)]
        print(f"{s}: evidence không nằm trọn trong chunk nào: {miss or 'không có'}")


if __name__ == "__main__":
    main()
