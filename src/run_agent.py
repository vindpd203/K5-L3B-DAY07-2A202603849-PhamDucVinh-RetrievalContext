"""Run the real GLM agent on data/cases.json and save traces.

    python -m src.run_agent --name baseline --retriever dense --strategy A --split dev
    python -m src.run_agent --name baseline --retriever dense --strategy A --split dev --ids d03 d16   # quick try
    (--split test requires --locked: only after the config is locked on dev)

Agent input = question text + the question's user-provided `filter` (if any). No gold, no expected answer.
Output: results/agent/<name>/config.json and traces_<split>.json (array; format for starter/agent_metrics.py:
query_id, status, events (one "search" event per retrieval call), citations) + answer, context, model calls,
tokens, latency, error. A provider/DB error is recorded as status "error", never replaced by a fake result.
After the run, gold is used ONLY to print Context Evidence Rate (evaluation, not agent input).
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "starter")
from agentic import run_agent  # noqa: E402  (starter loop, unchanged)

from src.agent import GLMController  # noqa: E402
from src.convert_questions import hit  # noqa: E402
from src.retrieval import (BM25Retriever, DenseRetriever, HybridRetriever, NeighborRetriever,  # noqa: E402
                           context_chunks)


def make_retriever(name, strategy, neighbors=0):
    if name == "dense":
        r = DenseRetriever(strategy)
    elif name in ("bm25", "bm25+bigram"):
        r = BM25Retriever(strategy, bigrams=name.endswith("bigram"))
    elif name == "hybrid":
        r = HybridRetriever(DenseRetriever(strategy), BM25Retriever(strategy, bigrams=True))
    else:
        raise ValueError(name)
    return NeighborRetriever(r, strategy, neighbors) if neighbors else r


def slim(events):
    """Keep full context text, but only id/rank/score/page for raw results (text is already in context)."""
    out = []
    for e in events:
        e = dict(e)
        if "results" in e:
            e["results"] = [{k: r[k] for k in ("id", "rank", "score", "page", "method")} for r in e["results"]]
        out.append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="config name, e.g. baseline")
    ap.add_argument("--retriever", choices=["dense", "bm25", "bm25+bigram", "hybrid"], required=True)
    ap.add_argument("--strategy", choices=["A", "B"], default="A")
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--budget", type=int, default=3000, help="context budget in characters (incl. headers)")
    ap.add_argument("--max-searches", type=int, default=3)
    ap.add_argument("--neighbors", type=int, default=0, help="add ±N neighbor chunks to each hit (0 = off)")
    ap.add_argument("--first-query", choices=["model", "original"], default="model",
                    help="original = first search uses the question verbatim")
    ap.add_argument("--ids", nargs="*", help="run only these question ids")
    ap.add_argument("--locked", action="store_true")
    args = ap.parse_args()
    if args.split == "test" and not args.locked:
        raise SystemExit("Test chỉ chạy sau khi chốt cấu hình trên dev: thêm --locked")

    cases = [c for c in json.loads(Path("data/cases.json").read_text(encoding="utf-8")) if c["split"] == args.split]
    questions = {q["id"]: q for q in json.loads(Path("data/questions.json").read_text(encoding="utf-8"))}
    if args.ids:
        cases = [c for c in cases if c["id"] in args.ids]
    retriever = make_retriever(args.retriever, args.strategy, args.neighbors)
    controller = GLMController(args.max_searches, first_query=args.first_query)

    out_dir = Path("results/agent") / args.name
    out_dir.mkdir(parents=True, exist_ok=True)
    config = {k: v for k, v in vars(args).items() if k not in ("ids", "locked")}
    config.update(retriever_impl=retriever.name, model_requested=controller.model, budget_unit="characters",
                  prompt="prompts/agent_system.md", loop="starter/agentic.py run_agent (unchanged)")
    (out_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    traces = []
    for c in cases:
        filters = (questions.get(c["id"]) or {}).get("filter")  # user-provided input, not gold
        controller.calls = []
        t = time.perf_counter()
        try:
            res = run_agent(c["question"], controller, retriever, filters=filters, max_searches=args.max_searches,
                            top_k=args.top_k, budget=args.budget)
            error = None
        except Exception as ex:  # provider / DB / malformed tool output
            res, error = {"status": "error", "answer": None, "citations": [], "events": []}, f"{type(ex).__name__}: {ex}"
        searches = [e for e in res["events"] if e.get("event") == "search"]
        last = searches[-1] if searches else {}
        calls = controller.calls
        traces.append({
            "query_id": c["id"], "split": c["split"], "question": c["question"], "answerable": c["answerable"],
            "filter": filters, "status": res["status"], "answer": res["answer"], "citations": res["citations"],
            "n_searches": len(searches), "queries": [e["query"] for e in searches],
            "final_context_ids": last.get("context_ids", []), "final_context": last.get("context", ""),
            "events": slim(res["events"]), "model_calls": calls,
            "model": sorted({m["model"] for m in calls if m.get("model")}),
            "prompt_tokens": sum(m["prompt_tokens"] or 0 for m in calls),
            "completion_tokens": sum(m["completion_tokens"] or 0 for m in calls),
            "latency_s": round(time.perf_counter() - t, 2), "error": error})
        tr = traces[-1]
        print(f"{c['id']:>4} {'có ĐA' if c['answerable'] else 'thiếu':5} -> {tr['status']:8} searches={tr['n_searches']} "
              f"cite={tr['citations']} {tr['latency_s']}s tok={tr['prompt_tokens']}+{tr['completion_tokens']}"
              + (f" ERROR {error}" if error else ""), flush=True)

    path = out_dir / f"traces_{args.split}.json"
    path.write_text(json.dumps(traces, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # ---- evaluation only (gold used here, after the agent finished) ----
    by_id = context_chunks(args.strategy, args.neighbors)
    ans = [t for t in traces if t["answerable"] and t["status"] != "error"]
    ctx_hit = [t["query_id"] for t in ans if any(hit(by_id[i], questions[t["query_id"]]["gold"]) for i in t["final_context_ids"])]
    ok = [t for t in traces if t["status"] != "error"]
    print(f"\nĐã lưu {path}")
    print(f"Context Evidence Rate: {len(ctx_hit)}/{len(ans)} | tool use: {sum(t['n_searches'] > 0 for t in ok)}/{len(ok)} | "
          f"answered: {sum(t['status'] == 'answered' for t in ok)}, abstain: {sum(t['status'] == 'abstain' for t in ok)}, "
          f"error: {len(traces) - len(ok)} | tokens: {sum(t['prompt_tokens'] for t in traces)}+"
          f"{sum(t['completion_tokens'] for t in traces)} | thời gian: {sum(t['latency_s'] for t in traces):.0f}s")


if __name__ == "__main__":
    main()
