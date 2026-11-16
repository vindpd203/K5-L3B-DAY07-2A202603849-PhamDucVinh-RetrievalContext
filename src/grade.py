"""Interactive manual grading of a reviews_<split>.json file (the human enters every label).

    python -m src.grade results/agent/bm25_A_nb/reviews_dev.json
    python -m src.grade results/agent/bm25_A_nb/reviews_dev.json --redo d04 d11   # re-grade some questions

Shows question, expected answer + evidence (grader aid), the agent answer and the FULL text the model saw for each
cited id; asks for answer_grade (0/1/2), true/false per citation, abstention_correct, and a reason.
Saves after every question, so you can quit (q) and resume later; already graded questions are skipped.
"""
import argparse
import json
import textwrap
from pathlib import Path

LINE = "─" * 100


def show(label, text, width=100):
    print(f"\n{label}")
    for para in str(text).split("\n"):
        print(textwrap.fill(para, width, initial_indent="  ", subsequent_indent="  ") if para.strip() else "")


def ask(prompt, allowed):
    while True:
        v = input(f"{prompt} [{'/'.join(allowed)}] > ").strip().lower()
        if v in allowed:
            return v


def done(r):
    if r["answerable"]:
        filled = r["answer_grade"] is not None
    else:
        filled = r["abstention_correct"] is not None
    return filled and all(v is not None for v in r["citation_support"]) and r.get("context_grade", 0) is not None


def grade_one(r, i, n):
    print(f"\n{LINE}\n[{i}/{n}] {r['query_id']} | {'CÓ đáp án' if r['answerable'] else 'THIẾU bằng chứng'} "
          f"| agent: {r['status']}\n{LINE}")
    show("CÂU HỎI:", r["question"])
    if r["answerable"]:
        show("ĐÁP ÁN CHUẨN (chỉ để chấm):", r["expected_answer_for_grader"])
        show("EVIDENCE CHUẨN:", " | ".join(r["evidence_for_grader"]))
    if "context_grade" in r:
        show("CONTEXT CUỐI GỬI MODEL (toàn bộ):", r.get("final_context") or "(trống)")
        v = ask("Chấm context: 0=không có evidence, 1=có nhưng thiếu điều kiện/nguồn, 2=đủ evidence và nguồn",
                ["0", "1", "2", "q"])
        if v == "q":
            return False
        r["context_grade"] = int(v)
    show("CÂU TRẢ LỜI CỦA AGENT:", r["answer"])

    support = []
    for k, cid in enumerate(r["citations"]):
        show(f"ĐOẠN ĐƯỢC TRÍCH {k + 1}/{len(r['citations'])} [{cid}] (đúng văn bản model đã thấy):", r["cited_text"][cid])
        hint = (r.get("hint_cited_chunk_has_gold_evidence") or [None] * len(r["citations"]))[k]
        print(f"  (gợi ý tự động: đoạn này {'CÓ' if hint else 'KHÔNG có'} nguyên văn evidence chuẩn — chỉ tham khảo)")
        v = ask(f"  Đoạn [{cid}] có thật sự hỗ trợ ý được trích trong câu trả lời? y=đúng n=sai", ["y", "n", "q"])
        if v == "q":
            return False
        support.append(v == "y")

    if r["answerable"]:
        if r["status"] == "abstain":
            print("\n  Agent từ chối câu có đáp án → answer_grade = 0 (theo BENCHMARK.md).")
            grade = 0
        else:
            v = ask("\nĐiểm câu trả lời: 0=sai/thiếu evidence, 1=đúng một phần, 2=đúng và đủ", ["0", "1", "2", "q"])
            if v == "q":
                return False
            grade = int(v)
        r["answer_grade"] = grade
    else:
        v = ask("\nAgent có thật sự từ chối, không khẳng định gì vô căn cứ? y=đúng n=sai", ["y", "n", "q"])
        if v == "q":
            return False
        r["abstention_correct"] = v == "y"
    r["citation_support"] = support
    reason = ""
    while len(reason) < 3:  # BENCHMARK.md: every label needs a reason
        reason = input("Lý do (bắt buộc, 1 câu, vd. 'đủ 2 ý: 10 ngày + tạm ngừng') > ").strip()
    r["reason"] = reason
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--redo", nargs="*", default=[])
    ap.add_argument("--need-reason", action="store_true", help="re-grade every question whose reason is empty")
    args = ap.parse_args()
    rows = json.loads(args.path.read_text(encoding="utf-8"))
    for r in rows:
        if r["query_id"] in args.redo or (args.need_reason and len(r["reason"].strip()) < 3):
            r["answer_grade"], r["abstention_correct"] = None, None
            r["citation_support"] = [None] * len(r["citations"])
            if "context_grade" in r:
                r["context_grade"] = None
    todo = [r for r in rows if not done(r)]
    print(f"{args.path}: {len(rows) - len(todo)}/{len(rows)} câu đã chấm, còn {len(todo)}. Gõ q để dừng (đã lưu).")
    for i, r in enumerate(todo, 1):
        if not grade_one(r, i, len(todo)):
            break
        args.path.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    left = sum(not done(r) for r in rows)
    print(f"\nĐã lưu. Còn {left} câu chưa chấm." if left else "\nĐã chấm xong tất cả.")
    ctx = [r["context_grade"] for r in rows if r.get("context_grade") is not None]
    if ctx:
        print(f"Context 0/1/2: {ctx.count(0)}/{ctx.count(1)}/{ctx.count(2)} (n={len(ctx)})")


if __name__ == "__main__":
    main()
