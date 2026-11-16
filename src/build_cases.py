"""T0.6: build data/cases.json = 20 answerable questions (from data/questions.json) + 4 no-evidence questions.

Each no-evidence question was checked with `python -m src.search_corpus <keywords>` on pages 1-32 (2026-11-16);
the keywords and what was found are recorded in absence_reason. Re-run that command to re-verify.
Dev and test no-evidence questions use different topics to avoid leakage.
"""
import json
from pathlib import Path

NO_EVIDENCE = [
    {"id": "d16", "split": "dev",
     "question": "Tổ chức lập hóa đơn điện tử sai thời điểm thì bị phạt tiền bao nhiêu?",
     "absence_reason": "Tìm 'phạt', 'phat', 'chế tài': 0 kết quả. 'vi phạm'/'xử lý vi' chỉ nhắc hành vi vi phạm "
                       "và dẫn chiếu Điều 41 NĐ 254/2026 (p8, p11, p12, p26), không có mức tiền phạt."},
    {"id": "d17", "split": "dev",
     "question": "Tổ chức cung cấp dịch vụ hóa đơn điện tử được thu giá dịch vụ tối đa bao nhiêu đồng cho mỗi hóa đơn?",
     "absence_reason": "Tìm 'giá dịch vụ': 0 kết quả. 'phí' chỉ có 'miễn phí dịch vụ' với hóa đơn có mã của cơ quan "
                       "thuế (p6, p10, p28) và phí bảo hiểm/thanh toán (p20, p21); 'đồng' không có giá theo hóa đơn."},
    {"id": "t06", "split": "test",
     "question": "Hóa đơn điện tử phải được lưu trữ trong thời hạn tối thiểu bao nhiêu năm?",
     "absence_reason": "Tìm 'thời hạn lưu', 'năm kể từ': 0 kết quả. 'lưu trữ' (15 kết quả) và 'lưu giữ' (3) chỉ nói "
                       "dịch vụ nhận, truyền, lưu trữ dữ liệu và lưu giữ văn bản thỏa thuận, không có thời hạn."},
    {"id": "t07", "split": "test",
     "question": "Thuế suất thuế giá trị gia tăng áp dụng cho dịch vụ cung cấp hóa đơn điện tử là bao nhiêu phần trăm?",
     "absence_reason": "Tìm '%', 'phần trăm': 0 kết quả. 'thuế suất' (p5, p17) chỉ là một trường nội dung trên hóa "
                       "đơn, không quy định mức thuế suất."},
]


def main():
    answerable = json.loads(Path("data/questions.json").read_text(encoding="utf-8"))
    cases = [{"id": q["id"], "split": q["split"], "question": q["question"], "answerable": True,
              "expected_behavior": "search_and_answer"} for q in answerable]
    cases += [{**q, "answerable": False, "expected_behavior": "search_and_abstain"} for q in NO_EVIDENCE]
    cases.sort(key=lambda c: (c["split"] != "dev", c["id"]))
    assert len({c["id"] for c in cases}) == len(cases), "duplicate id"
    Path("data/cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for split in ("dev", "test"):
        s = [c for c in cases if c["split"] == split]
        print(f"{split}: {len(s)} câu ({sum(c['answerable'] for c in s)} có đáp án, "
              f"{sum(not c['answerable'] for c in s)} thiếu bằng chứng)")


if __name__ == "__main__":
    main()
