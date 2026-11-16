"""Write the grader-approved labels from results/agent/grades_{dev,test}.md into the reviews_<split>.json files.

Origin of labels (disclose in the report): AI (Claude) drafted them after reading every answer, cited window and context;
the grader (Phạm Đức Vinh) reviewed both draft files and adopted them as the official labels on 2026-11-16.
Dev labels replace the grader's earlier first-pass labels (kept in git history if committed; differences listed in
grades_dev.md). Citation labels: one bool per citation id, in the trace's citation order.

    python -m src.fill_labels
"""
import json
from pathlib import Path

ROOT = Path("results/agent")
T, F = True, False
ABST_OK = "Chỉ nói không đủ bằng chứng, không đưa số liệu hay khẳng định nào."

# query_id: (answer_grade | None, citation_support, context_grade | None, abstention_correct | None, reason)
LABELS = {
    ("dense_A", "test"): {
        "t01": (1, [F, T, F], 2, None, "Đúng 'Có' + đủ 2 ngoại lệ (p011:00), nhưng câu hậu quả ngược văn bản: p008:02 bị cắt mất "
                                    "'người nộp thuế không thuộc trường hợp' (ở p008:00); p001:04 chỉ là phạm vi điều chỉnh."),
        "t02": (2, [T], 2, None, "'Không quá 150 tỷ đồng/năm' đúng nguyên văn, có nguồn p025:05."),
        "t03": (0, [], 1, None, "Từ chối nhầm; context chỉ có ý phụ 'gia hạn mỗi lần không quá 12 tháng', thiếu 'thời hạn 12 tháng' (p031:01)."),
        "t04": (0, [], 1, None, "Từ chối nhầm; context (p029:06) chỉ có nửa sau evidence, nửa đầu 'gồm hai thành phần' bị cắt ở chunk trước."),
        "t05": (0, [], 0, None, "Từ chối nhầm; context không có Điều 25 'hiệu lực thi hành kể từ ngày 01 tháng 7 năm 2026'."),
        "t06": (None, [], None, T, ABST_OK),
        "t07": (None, [], None, T, ABST_OK),
    },
    ("bm25_A_nb", "test"): {
        "t01": (2, [T, T], 2, None, "'Có' + đủ 2 ngoại lệ; hậu quả đúng văn bản: trong 01 ngày ra Thông báo giải trình, bổ sung (p008:04)."),
        "t02": (2, [T, T], 2, None, "'Không quá 150 tỷ đồng/năm'; cả 2 cửa sổ đều chứa khoản 3 Điều 13."),
        "t03": (2, [T, T], 2, None, "Đủ: 12 tháng hoặc theo đề nghị ≤ 12 tháng; gia hạn mỗi lần ≤ 12 tháng; ý thêm đều có trong đoạn trích."),
        "t04": (2, [T], 2, None, "Đúng 2 thành phần (dữ liệu nghiệp vụ + chữ ký số), nguồn Điều 18; hiểu đúng câu hỏi thiếu chữ 'chứng từ'."),
        "t05": (2, [T], 2, None, "'01 tháng 7 năm 2026' (Điều 25 khoản 1); ý về văn bản hết hiệu lực có trong đoạn trích."),
        "t06": (None, [], None, T, ABST_OK),
        "t07": (None, [], None, T, ABST_OK),
    },
    ("bm25_A_nb", "dev"): {
        "d01": (2, [T], None, None, "XML (eXtensible Markup Language) đúng nguyên văn Điều 3."),
        "d02": (2, [T, T], None, None, "Tối thiểu 5 Mbps mỗi kênh truyền, kèm điều kiện kênh chính + dự phòng; cả 2 cửa sổ chứa khoản 4."),
        "d03": (2, [T], None, None, "Nhóm sáu ký tự gồm chữ viết và chữ số; câu dẫn Phụ lục I có trong đoạn."),
        "d04": (2, [T, T], None, None, "Đủ 3 ý: tiếng Việt + tiếng Anh, vị trí (ngoặc đơn/dưới dòng), cỡ chữ bằng hoặc nhỏ hơn."),
        "d05": (2, [T, T, T], None, None, "01 ngày làm việc kể từ ngày tiếp nhận; các bước khớp/không khớp có trong đoạn trích."),
        "d06": (2, [T, T], None, None, "03 ngày làm việc kể từ khi nhận Thông báo giải trình; bối cảnh 01 ngày và không chấp nhận đúng."),
        "d07": (2, [T, T, T, T], None, None, "Có (điểm c khoản 1 Điều 8); điều kiện tiếp tục sử dụng (khoản 3) và thủ tục đều có nguồn."),
        "d08": (2, [T], None, None, "Đủ 2 ý: 10 ngày làm việc + quá hạn thì tạm ngừng sử dụng hóa đơn."),
        "d09": (2, [T, T], None, None, "Đủ 2 ý chính: bằng văn bản (hợp đồng/thỏa thuận), trừ bán tài sản thi hành án; phần thêm có nguồn p016."),
        "d10": (2, [T, T], None, None, "Đủ 3 ý: thông báo người mua, không lập lại, thông báo CQT Mẫu 04/SS-HĐĐT; ý p021:06 thừa nhưng không sai."),
        "d11": (2, [T, T, T, T], None, None, "Sai mã số thuế → được chọn điều chỉnh hoặc thay thế (p017:01); các ý thêm đúng nguồn."),
        "d12": (2, [T, T], None, None, "Đủ 3 trường hợp không bắt buộc lập văn bản thỏa thuận (p018:00–01)."),
        "d13": (2, [T], None, None, "'Không dưới 05 tỷ đồng' đúng nguyên văn; đáp án chỉ có 1 ý."),
        "d14": (2, [T], None, None, "Đủ 2 ý: tối thiểu 20 km + sẵn sàng hoạt động khi hệ thống chính gặp sự cố."),
        "d15": (2, [T, T], None, None, "Không phải lập lại; thông báo bên nhận + CQT Mẫu 04/SS-CTĐT; khoản 2 thay thế đúng."),
        "d16": (None, [], None, T, ABST_OK),
        "d17": (None, [], None, T, ABST_OK),
    },
    ("hybrid_A_oq_nb", "dev"): {
        "d01": (2, [T], None, None, "XML đúng nguyên văn; ý về 2–3 thành phần định dạng có trong đoạn."),
        "d02": (2, [T], None, None, "Tối thiểu 5 Mbps mỗi kênh truyền, kèm điều kiện kết nối."),
        "d03": (2, [T], None, None, "Nhóm sáu ký tự gồm chữ viết và chữ số."),
        "d04": (2, [T, T], None, None, "Đủ 3 ý: tiếng Việt + tiếng Anh, vị trí, cỡ chữ bằng hoặc nhỏ hơn."),
        "d05": (2, [T], None, None, "01 ngày làm việc kể từ ngày tiếp nhận đăng ký."),
        "d06": (1, [T, T, T, T], None, None, "Ý chính đúng (03 ngày, p008:05) nhưng phần 'Cụ thể' lấy từ thủ tục khác (giải trình khi đang "
                                            "sử dụng hóa đơn, p013:07/p014:02), trình bày như cùng thủ tục đăng ký."),
        "d07": (2, [T, T, T, T], None, None, "Có (điểm c khoản 1 Điều 8); được tiếp tục sử dụng sau khi thông báo (khoản 3)."),
        "d08": (2, [T], None, None, "Đủ 2 ý: 10 ngày làm việc + quá hạn thì tạm ngừng sử dụng hóa đơn."),
        "d09": (2, [T, T, T], None, None, "Bằng văn bản, ngoại lệ bán tài sản thi hành án; nội dung văn bản ủy nhiệm có nguồn."),
        "d10": (2, [T, T], None, None, "Đủ 3 ý: thông báo người mua, không lập lại, thông báo CQT Mẫu 04/SS-HĐĐT."),
        "d11": (2, [T, T, T, T, T], None, None, "Sai mã số thuế → được chọn điều chỉnh hoặc thay thế (p017:01); các ý thêm đúng nguồn."),
        "d12": (2, [T, T], None, None, "Đủ 3 trường hợp không bắt buộc lập văn bản thỏa thuận."),
        "d13": (2, [T], None, None, "'Không dưới 05 tỷ đồng' đúng nguyên văn."),
        "d14": (2, [T], None, None, "Đủ 2 ý: tối thiểu 20 km + sẵn sàng hoạt động khi hệ thống chính gặp sự cố."),
        "d15": (2, [T], None, None, "Không phải lập lại; thông báo bên nhận + CQT Mẫu 04/SS-CTĐT."),
        "d16": (None, [], None, T, ABST_OK),
        "d17": (None, [], None, T, ABST_OK),
    },
}


def main():
    for (name, split), labels in LABELS.items():
        path = ROOT / name / f"reviews_{split}.json"
        rows = json.loads(path.read_text(encoding="utf-8"))
        assert {r["query_id"] for r in rows} == set(labels), f"{path}: question ids differ"
        for r in rows:
            grade, support, ctx, abst, reason = labels[r["query_id"]]
            assert len(support) == len(r["citations"]), f"{path} {r['query_id']}: {len(r['citations'])} citations"
            assert r["answerable"] == (abst is None), f"{path} {r['query_id']}: answerable mismatch"
            if r["status"] == "abstain" and r["answerable"]:
                assert grade == 0, f"{path} {r['query_id']}: abstain on answerable must be 0"
            r.update(answer_grade=grade, citation_support=support, abstention_correct=abst, reason=reason)
            if "context_grade" in r:
                assert ctx is not None, f"{path} {r['query_id']}: context grade required"
                r["context_grade"] = ctx
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{path}: {len(rows)} nhãn")


if __name__ == "__main__":
    main()
