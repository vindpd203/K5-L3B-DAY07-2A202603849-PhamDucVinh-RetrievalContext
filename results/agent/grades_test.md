> Bảng điểm đánh giá chính thức của người chấm (Phạm Đức Vinh) trong
> `results/agent/{dense_A,bm25_A_nb}/reviews_test.json`. Ngày 2026-11-16. Thang answer 0/1/2 theo BENCHMARK.md.

## Tổng hợp

| Tiêu chí | dense_A (baseline) | bm25_A_nb (đã chọn) |
|---|---|---|
| Answer 0/1/2 | 3 / 1 / 1 → **0,60** | 0 / 0 / 5 → **2,00** |
| Context 0/1/2 | 1 / 2 / 2 → **1,20** | 0 / 0 / 5 → **2,00** |
| Citation hỗ trợ | 2/4 đạt (50%) | 8/8 đạt (100%) |
| Abstention t06, t07 | 2/2 từ chối đúng | 2/2 từ chối đúng |
| Từ chối sai (False abstain) | 3/5 câu (t03, t04, t05) | 0/5 câu (0%) |
| Kết luận | Baseline đối chứng | **Vượt trội (Được chọn)** |

## Đánh giá chi tiết các câu trả lời cụ thể

| Câu | Cấu hình | Đáp án chuẩn | Agent trả lời | Điểm | Lý do chấm |
|---|---|---|---|---|---|
| t01 | dense_A | Có, là dấu hiệu rủi ro cao, trừ 2 ngoại lệ (kinh doanh, cá nhân KD) | Đúng "Có" + 2 ngoại lệ, nhưng kết luận hậu quả ngược | 1 | Đúng "Có" + đủ 2 ngoại lệ (p011:00). Nhưng câu hậu quả ngược với văn bản: chunk p008:02 bị cắt mất cụm "người nộp thuế không thuộc trường hợp…", dẫn đến agent nói rủi ro cao thì được chấp nhận ngay (thực tế phải giải trình, bổ sung trong 01 ngày). |
| t01 | bm25_A_nb | Có, là dấu hiệu rủi ro cao, trừ 2 ngoại lệ (kinh doanh, cá nhân KD) | Đủ "Có" + 2 ngoại lệ + hậu quả giải trình 01 ngày | 2 | Đúng "Có" + đủ 2 ngoại lệ; hậu quả đúng văn bản: trong 01 ngày làm việc cơ quan thuế ra Thông báo giải trình, bổ sung (p008:04). |
| t02 | dense_A | Không quá 150 tỷ đồng/năm | "Không quá 150 tỷ đồng/năm" | 2 | "Không quá 150 tỷ đồng/năm" đúng nguyên văn, có nguồn (p025:05). |
| t02 | bm25_A_nb | Không quá 150 tỷ đồng/năm | "Không quá 150 tỷ đồng/năm" | 2 | "Không quá 150 tỷ đồng/năm" đúng nguyên văn; cả 2 cửa sổ đều chứa khoản 3 Điều 13 (p025:04, p025:06). |
| t03 | dense_A | 12 tháng (hoặc theo đề nghị ≤ 12 tháng); mỗi lần gia hạn ≤ 12 tháng | Từ chối trả lời (thiếu thông tin) | 0 | Từ chối nhầm (false abstain). Context chỉ có ý phụ "gia hạn mỗi lần không quá 12 tháng" (p031:03/04), thiếu câu chính "thời hạn sử dụng 12 tháng" (p031:01). |
| t03 | bm25_A_nb | 12 tháng (hoặc theo đề nghị ≤ 12 tháng); mỗi lần gia hạn ≤ 12 tháng | Đầy đủ thời hạn 12 tháng và điều kiện gia hạn | 2 | Đủ: 12 tháng hoặc theo đề nghị ≤ 12 tháng; gia hạn mỗi lần ≤ 12 tháng. Ý thêm (cảnh báo 30 ngày, thu hồi khi 06 tháng không tra cứu) đều có trong đoạn trích (p031:01, p031:04). |
| t04 | dense_A | 2 thành phần: dữ liệu nghiệp vụ và dữ liệu chữ ký số | Từ chối trả lời (thiếu thông tin) | 0 | Từ chối nhầm (false abstain). Context (p029:06) chỉ có nửa sau, nửa đầu "gồm hai thành phần: thành phần chứa dữ liệu nghiệp vụ" bị cắt ở chunk trước. |
| t04 | bm25_A_nb | 2 thành phần: dữ liệu nghiệp vụ và dữ liệu chữ ký số | Đủ 2 thành phần nghiệp vụ và chữ ký số | 2 | Đúng 2 thành phần (dữ liệu nghiệp vụ + chữ ký số), có nguồn Điều 18 (p029:05). Hiểu đúng câu hỏi thiếu chữ "chứng từ". |
| t05 | dense_A | Từ ngày 01 tháng 7 năm 2026 | Từ chối trả lời (thiếu thông tin) | 0 | Từ chối nhầm (false abstain). Context không có Điều 25 về ngày có hiệu lực thi hành 01/07/2026. |
| t05 | bm25_A_nb | Từ ngày 01 tháng 7 năm 2026 | Đúng ngày 01 tháng 7 năm 2026 | 2 | "01 tháng 7 năm 2026" (Điều 25 khoản 1, p032:05); ý thêm về các văn bản hết hiệu lực có trong đoạn trích. |

## Ghi chú citation

- **dense_A**:
  - Gặp lỗi trích dẫn ở câu **t01**: p001:04 sai (chỉ là phạm vi điều chỉnh Điều 1, không chứa tiêu chí), p008:02 bị cắt mất ngữ cảnh phủ định. Chỉ có p011:00 và p025:05 đúng → Citation hỗ trợ đạt 2/4 (50%).
  - Các câu **t03, t04, t05** do từ chối nhầm nên không có citation.
- **bm25_A_nb**:
  - Nhờ cơ chế neighbors (±1) mở rộng context, các đoạn trích chứa đầy đủ căn cứ điều khoản. Toàn bộ 8/8 citation đều hỗ trợ chính xác cho nội dung trả lời (100%).
- **Câu t06, t07 (kiểm tra từ chối)**: Cả hai cấu hình đều từ chối đúng (chỉ nêu không đủ thông tin, không tự suy diễn số liệu).

## Bảng điểm chi tiết 5 câu test và 2 câu kiểm tra từ chối

| Câu | dense_A (baseline) | bm25_A_nb (đã chọn) |
|---|---|---|
| t01 | 1 | 2 |
| t02 | 2 | 2 |
| t03 | 0 | 2 |
| t04 | 0 | 2 |
| t05 | 0 | 2 |
| t06 / t07 | từ chối đúng / đúng | từ chối đúng / đúng |
