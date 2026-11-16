"""T1.4: retrieval benchmark (no LLM). Same corpus, index version, questions and hit rule for every method.

    python -m src.eval_retrieval --split dev --strategy A B
    python -m src.eval_retrieval --split test --strategy A --locked   # only after the config is locked on dev

Metrics over answerable questions only (no-evidence questions are not in data/questions.json):
Hit@1, Evidence Hit@3, Hit@5 (n/N), MRR@10, search time per query (ms). Cost = 0 (local embedding, local DB).
Output: results/retrieval/<split>_<strategy>.json (summary + per-query top-10 trace with hit flags).
"""
import argparse
import json
import statistics
import time
from pathlib import Path

from src.convert_questions import hit
from src.retrieval import BM25Retriever, DenseRetriever, HybridRetriever, NeighborRetriever

TOP = 10
METHODS = ["dense", "bm25", "bm25+bigram", "hybrid", "bm25+nb"]


def build(strategy, embedder, methods):
    dense = DenseRetriever(strategy, embedder)
    bm25, bm25_bi = BM25Retriever(strategy), BM25Retriever(strategy, bigrams=True)
    all_ = {"dense": dense, "bm25": bm25, "bm25+bigram": bm25_bi, "hybrid": HybridRetriever(dense, bm25_bi),
            "bm25+nb": NeighborRetriever(bm25, strategy, 1)}  # hit judged on the window text the model sees
    return [all_[m] for m in methods]


def evaluate(retriever, questions):
    traces, times = [], []
    for q in questions:
        t = time.perf_counter()
        results = retriever.search(q["question"], filters=q.get("filter"), top_k=TOP)  # original query, no rewrite
        times.append((time.perf_counter() - t) * 1000)
        flags = [hit(r, q["gold"]) for r in results]
        first = next((i + 1 for i, f in enumerate(flags) if f), None)
        traces.append({"id": q["id"], "question": q["question"], "filter": q.get("filter"), "first_hit_rank": first,
                       "results": [{"rank": r["rank"], "id": r["id"], "page": r["page"], "score": r["score"],
                                    "chapter": r["metadata"].get("chapter"), "article": r["metadata"].get("article"),
                                    "hit": f} for r, f in zip(results, flags)]})
    n = len(questions)
    at = lambda k: sum(1 for t in traces if t["first_hit_rank"] and t["first_hit_rank"] <= k)
    summary = {"method": retriever.name, "N": n, "hit@1": at(1), "hit@3": at(3), "hit@5": at(5),
               "mrr@10": round(sum(1 / t["first_hit_rank"] for t in traces if t["first_hit_rank"]) / n, 3),
               "ms_median": round(statistics.median(times), 1), "ms_mean": round(statistics.mean(times), 1),
               "miss@3": [t["id"] for t in traces if not (t["first_hit_rank"] and t["first_hit_rank"] <= 3)]}
    return summary, traces


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--strategy", nargs="+", default=["A", "B"], choices=["A", "B"])
    ap.add_argument("--locked", action="store_true", help="required for --split test (config locked on dev)")
    ap.add_argument("--methods", nargs="+", choices=METHODS, default=METHODS[:4])
    args = ap.parse_args()
    if args.split == "test" and not args.locked:
        raise SystemExit("Test chỉ chạy sau khi chốt cấu hình trên dev: thêm --locked")

    from src.embeddings import SentenceTransformerEmbedder
    embedder = SentenceTransformerEmbedder()
    questions = [q for q in json.loads(Path("data/questions.json").read_text(encoding="utf-8"))
                 if q["split"] == args.split]
    out_dir = Path("results/retrieval")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"| Chunk | Method | Hit@1 | Evidence Hit@3 | Hit@5 | MRR@10 | ms/query (median) | Trượt @3 |")
    print("|---|---|---|---|---|---|---|---|")
    for s in args.strategy:
        report = {"split": args.split, "strategy": s, "embedding": embedder.model_name, "top_k_logged": TOP,
                  "hit_rule": "same source, gold page in chunk pages, evidence substring after whitespace collapse",
                  "query": "original question, filter only when the question has one", "runs": []}
        for r in build(s, embedder, args.methods):
            r.search("khởi động", top_k=1)  # warm-up so the first timed query is fair
            summary, traces = evaluate(r, questions)
            report["runs"].append({"summary": summary, "traces": traces})
            N = summary["N"]
            print(f"| {s} | {summary['method']} | {summary['hit@1']}/{N} | {summary['hit@3']}/{N} | "
                  f"{summary['hit@5']}/{N} | {summary['mrr@10']} | {summary['ms_median']} | "
                  f"{', '.join(summary['miss@3']) or '-'} |")
        path = out_dir / f"{args.split}_{s}{'' if args.methods == METHODS[:4] else '_' + '_'.join(args.methods).replace('+', '-')}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nTrace: {out_dir}/{args.split}_<strategy>.json")


if __name__ == "__main__":
    main()
