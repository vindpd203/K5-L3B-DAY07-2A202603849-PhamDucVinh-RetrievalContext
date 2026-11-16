> Đây là nhãn chính thức.
> vào `results/agent/{dense_A,bm25_A_nb}/reviews_test.json`. Có thể dùng bản này để đối chiếu và tự ghi vào file nếu cần
> Ngày: 2026-11-16. Thang: context 0/1/2 và answer 0/1/2 theo BENCHMARK.md.

## dense_A (baseline)

| Câu | Context | Citation hỗ trợ | Answer | Lý do |
|---|---|---|---|---|
| t01 | 2 | p001:04 **sai** · p011:00 đúng · p008:02 **sai** | **1** | Đúng "Có" + đủ 2 ngoại lệ (p011:00). Nhưng câu "hậu quả" **ngược với văn bản**: p008:02 bị cắt mất cụm "người nộp thuế **không thuộc** trường hợp…" ở p008:00, nên agent nói rủi ro cao thì được chấp nhận ngay — thực tế là phải giải trình, bổ sung trong 01 ngày. p001:04 chỉ là phạm vi điều chỉnh (Điều 1), không chứa tiêu chí. |
| t02 | 2 | p025:05 đúng | 2 | "Không quá 150 tỷ đồng/năm" đúng nguyên văn, có nguồn. |
| t03 | 1 | — | 0 (tự động) | Từ chối nhầm. Context chỉ có ý phụ "gia hạn mỗi lần không quá 12 tháng" (p031:03/04), thiếu câu chính "thời hạn sử dụng 12 tháng" (p031:01). |
| t04 | 1 | — | 0 (tự động) | Từ chối nhầm. Context (p029:06) chỉ có nửa sau "…và thành phần chứa dữ liệu chữ ký số"; nửa đầu "gồm hai thành phần: thành phần chứa dữ liệu nghiệp vụ" bị cắt ở chunk trước. |
| t05 | 0 | — | 0 (tự động) | Từ chối nhầm. Context không có Điều 25 / "hiệu lực thi hành kể từ ngày 01 tháng 7 năm 2026". |
| t06 | — | — | abstention **đúng** | Chỉ nói không đủ bằng chứng, không đưa số năm. |
| t07 | — | — | abstention **đúng** | Chỉ nói không đủ bằng chứng, không đưa thuế suất. |

Tổng nháp: answer 0/1/2 = **3 / 1 / 1 → 0,60/2** · citation 2/4 · context 0/1/2 = 1 / 2 / 2 · abstention 2/2.

## bm25_A_nb (đã chọn)

| Câu | Context | Citation hỗ trợ | Answer | Lý do |
|---|---|---|---|---|
| t01 | 2 | p011:00 đúng · p008:04 đúng | 2 | "Có" + đủ 2 ngoại lệ; hậu quả đúng văn bản: trong 01 ngày làm việc cơ quan thuế ra Thông báo giải trình, bổ sung (p008:04). |
| t02 | 2 | p025:04 đúng · p025:06 đúng | 2 | "Không quá 150 tỷ đồng/năm"; cả 2 cửa sổ đều chứa khoản 3 Điều 13. |
| t03 | 2 | p031:01 đúng · p031:04 đúng | 2 | Đủ: 12 tháng hoặc theo đề nghị ≤ 12 tháng; gia hạn mỗi lần ≤ 12 tháng. Ý thêm (cảnh báo 30 ngày, thu hồi khi 06 tháng không tra cứu) đều có trong đoạn trích. |
| t04 | 2 | p029:05 đúng | 2 | Đúng 2 thành phần (dữ liệu nghiệp vụ + chữ ký số), có nguồn Điều 18. Câu hỏi viết "Định dạng điện tử" (thiếu "chứng từ") — agent hiểu đúng ý. |
| t05 | 2 | p032:05 đúng | 2 | "01 tháng 7 năm 2026" (Điều 25 khoản 1); ý thêm về các văn bản hết hiệu lực có trong đoạn trích. |
| t06 | — | — | abstention **đúng** | Chỉ nói không đủ bằng chứng. |
| t07 | — | — | abstention **đúng** | Chỉ nói không đủ bằng chứng. |

Tổng nháp: answer 0/1/2 = **0 / 0 / 5 → 2,00/2** · citation 8/8 · context 0/1/2 = 0 / 0 / 5 · abstention 2/2.

