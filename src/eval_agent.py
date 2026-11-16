"""Compare agent runs (automatic metrics) and create manual review files.

    python -m src.eval_agent --split dev dense_A bm25_A hybrid_A          # comparison table
    python -m src.eval_agent --split dev --review hybrid_A                 # create reviews_dev.json to label by hand

Automatic (gold used only here, after the runs): Context Evidence Rate, first-search Evidence Hit@3, tool use,
search-count distribution, answered/abstain/error, abstention by status, false abstention, tokens, time.
Answer correctness and citation support are NOT judged here: they come from human labels in reviews_<split>.json,
aggregated with starter/agent_metrics.py.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from src.convert_questions import hit
from src.retrieval import context_chunks

ROOT = Path("results/agent")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarize(name, split, questions):
    config = load(ROOT / name / "config.json")
    traces = load(ROOT / name / f"traces_{split}.json")
    chunks = context_chunks(config["strategy"], config.get("neighbors", 0))
    ok = [t for t in traces if t["status"] != "error"]
    ans = [t for t in ok if t["answerable"]]
    una = [t for t in ok if not t["answerable"]]
    gold = lambda t: questions[t["query_id"]]["gold"]
    first_ids = lambda t: [r["id"] for r in next((e["results"] for e in t["events"] if e.get("event") == "search"), [])][:3]
    return {
        "name": name, "config": config, "N": len(traces), "errors": [t["query_id"] for t in traces if t["status"] == "error"],
        "context_evidence": [t["query_id"] for t in ans if any(hit(chunks[i], gold(t)) for i in t["final_context_ids"])],
        "first_search_hit3": [t["query_id"] for t in ans if any(hit(chunks[i], gold(t)) for i in first_ids(t))],
        "N_ans": len(ans), "N_una": len(una), "ans_ids": [t["query_id"] for t in ans],
        "tool_use": sum(t["n_searches"] > 0 for t in ok), "N_ok": len(ok),
        "searches": dict(sorted(Counter(t["n_searches"] for t in ok).items())),
        "answered": sum(t["status"] == "answered" for t in ok), "abstain": sum(t["status"] == "abstain" for t in ok),
        "una_abstained": [t["query_id"] for t in una if t["status"] == "abstain"],
        "false_abstain": [t["query_id"] for t in ans if t["status"] == "abstain"],
        "answers_with_citation": sum(bool(t["citations"]) for t in ok if t["status"] == "answered"),
        "citations": sum(len(t["citations"]) for t in ok),
        "tokens_in": sum(t["prompt_tokens"] for t in traces), "tokens_out": sum(t["completion_tokens"] for t in traces),
        "time_s": round(sum(t["latency_s"] for t in traces)),
        "models": sorted({m for t in traces for m in t.get("model", [])}),
    }


def table(rows):
    print("| Cấu hình | Context Evidence Rate | Hit@3 lần search đầu | Tool use | Số lần search | Answered / Abstain / Error "
          "| Từ chối đúng (thiếu BC) | Từ chối nhầm | Câu trả lời có citation | Token in+out | Thời gian |")
    print("|" + "---|" * 11)
    for r in rows:
        print(f"| {r['name']} | {len(r['context_evidence'])}/{r['N_ans']} | {len(r['first_search_hit3'])}/{r['N_ans']} | "
              f"{r['tool_use']}/{r['N_ok']} | {r['searches']} | {r['answered']} / {r['abstain']} / {len(r['errors'])} | "
              f"{len(r['una_abstained'])}/{r['N_una']} | {len(r['false_abstain'])}/{r['N_ans']} "
              f"{r['false_abstain'] or ''} | {r['answers_with_citation']}/{r['answered']} | "
              f"{r['tokens_in']}+{r['tokens_out']} | {r['time_s']}s |")
    for r in rows:
        missing = sorted(set(r["ans_ids"]) - set(r["context_evidence"]))
        print(f"- {r['name']}: context thiếu evidence: {missing or 'không'}; lỗi API: {r['errors'] or 'không'}; "
              f"model: {', '.join(r['models'])}")


def make_review(name, split, questions):
    path = ROOT / name / f"reviews_{split}.json"
    if path.exists():
        raise SystemExit(f"{path} đã tồn tại — không ghi đè nhãn đã chấm")
    config = load(ROOT / name / "config.json")
    chunks = context_chunks(config["strategy"], config.get("neighbors", 0))
    rows = []
    for t in load(ROOT / name / f"traces_{split}.json"):
        if t["status"] == "error":
            continue
        q = questions.get(t["query_id"])
        rows.append({
            "query_id": t["query_id"], "answerable": t["answerable"], "status": t["status"],
            "question": t["question"],
            "expected_answer_for_grader": q["expected_answer"] if q else None,  # grader aid, never agent input
            "evidence_for_grader": [g["evidence"] for g in q["gold"]] if q else None,
            "answer": t["answer"],
            "citations": t["citations"],
            "cited_text": {i: chunks[i]["text"] for i in t["citations"]},
            "hint_cited_chunk_has_gold_evidence": [hit(chunks[i], q["gold"]) for i in t["citations"]] if q else None,
            "final_context": t["final_context"],
            # ---- người chấm điền ----
            "answer_grade": None,                                     # câu có đáp án: 0/1/2 (abstain = 0)
            "citation_support": [None] * len(t["citations"]),        # true/false cho từng citation (đọc cited_text)
            "abstention_correct": None,                               # câu thiếu bằng chứng: true/false
            "reason": "",
        })
        if split == "test" and t["answerable"]:  # BENCHMARK.md §2: context 0/1/2 on test answerable questions
            rows[-1]["context_grade"] = None
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Đã tạo {path} ({len(rows)} câu). Điền answer_grade / citation_support / abstention_correct / reason, rồi chạy:")
    print(f"python starter/agent_metrics.py --cases data/cases.json --traces {ROOT / name / f'traces_{split}.json'} "
          f"--reviews {path} --split {split} --output {ROOT / name / f'agent_metrics_{split}.json'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--review", help="config name to create a manual review file for")
    args = ap.parse_args()
    questions = {q["id"]: q for q in load("data/questions.json")}
    if args.review:
        return make_review(args.review, args.split, questions)
    rows = []
    rows = [summarize(n, args.split, questions) for n in args.names]
    table(rows)
    out = ROOT / f"summary_{args.split}.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nĐã lưu {out}")


if __name__ == "__main__":
    main()
