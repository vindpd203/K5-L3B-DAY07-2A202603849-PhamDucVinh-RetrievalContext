> Đây là bản Nhãn chính thức là của người chấm (Phạm Đức Vinh) trong
> `results/agent/{bm25_A_nb,hybrid_A_oq_nb}/reviews_dev.json`. Bản này làm SAU khi người chấm đã chấm xong dev,
> để kiểm tra độ nhất quán. Ngày 2026-11-16. Thang answer 0/1/2 theo BENCHMARK.md.

## Tổng hợp

| | Người chấm | AI nháp |
|---|---|---|
| bm25_A_nb answer 0/1/2 | 0 / 3 / 12 → **1,80** | 0 / 0 / 15 → **2,00** |
| hybrid_A_oq_nb answer 0/1/2 | 0 / 5 / 10 → **1,67** | 0 / 1 / 14 → **1,93** |
| Citation | 30/30 và 30/30 | đồng ý (xem ghi chú d06, d10) |
| Abstention d16, d17 | 2/2 và 2/2 | đồng ý |
| Cấu hình thắng tiêu chí 3 | bm25_A_nb | bm25_A_nb (**không đổi lựa chọn**) |

## Câu lệch nhau (người chấm 1, AI 2)

| Câu | Cấu hình | Đáp án chuẩn | Agent trả lời | Vì sao AI cho 2 |
|---|---|---|---|---|
| d09 | bm25_A_nb | Có, bằng văn bản (hợp đồng/thỏa thuận), trừ bán tài sản thi hành án | Có + đúng ngoại lệ + thêm nội dung bắt buộc của hợp đồng ủy nhiệm (đúng p016) | Đủ cả 2 ý chính, phần thêm có nguồn. hybrid d09 gần giống được chấm 2. |
| d13 | cả hai | Không dưới 05 tỷ đồng | "không dưới 05 tỷ đồng" (nguyên văn) | Đúng và đủ — đáp án chỉ có 1 ý. |
| d14 | cả hai | Tối thiểu 20 km, sẵn sàng hoạt động khi hệ thống chính gặp sự cố | "tối thiểu 20 km và sẵn sàng hoạt động khi hệ thống chính gặp sự cố" | Đủ cả 2 ý. |
| d04 | hybrid_A_oq_nb | Tiếng Việt + tiếng Anh; tiếng Anh bên phải trong ngoặc đơn hoặc dưới dòng, cỡ chữ bằng/nhỏ hơn | Đủ cả 3 ý | bm25 d04 cùng nội dung được chấm 2. |
| d10 | hybrid_A_oq_nb | Thông báo người mua, không lập lại, thông báo CQT Mẫu 04/SS-HĐĐT | Đủ cả 3 ý | bm25 d10 cùng nội dung được chấm 2. |

Nếu người chấm có tiêu chí riêng cho các câu này (ví dụ trừ điểm câu trả lời quá dài, hoặc thiếu số Điều), nên ghi tiêu
chí đó vào `reason` và áp dụng giống nhau cho cả hai cấu hình.

## Ghi chú citation

- **bm25 d10** — citation p021:06 ("các lần xử lý tiếp theo theo hình thức đã áp dụng lần đầu") đúng chữ, nhưng ý này chỉ
  áp dụng cho điều chỉnh/thay thế, không liên quan trường hợp "chỉ thông báo" của câu hỏi. Không sai, chỉ thừa → vẫn 2.
- Các citation còn lại đã đối chiếu theo ý chính; các ý phụ trong câu trả lời dài (d05, d07, d11 của cả hai) được kiểm
  theo mẫu (p014:05 khoản 3 Điều 8, p009:00 không chấp nhận đăng ký, p019:01 thông báo rà soát) — đều có trong đoạn trích.

## 15 câu, 

| Câu | bm25_A_nb | hybrid_A_oq_nb |
|---|---|---|
| d01 | 2 | 2 |
| d02 | 2 | 2 |
| d03 | 2 | 2 |
| d04 | 2 | 2 (bạn: 1) |
| d05 | 2 | 2 |
| d06 | 2 | 1 |
| d07 | 2 | 2 |
| d08 | 2 | 2 |
| d09 | 2 (bạn: 1) | 2 |
| d10 | 2 | 2 (bạn: 1) |
| d11 | 2 | 2 |
| d12 | 2 | 2 |
| d13 | 2 (bạn: 1) | 2 (bạn: 1) |
| d14 | 2 (bạn: 1) | 2 (bạn: 1) |
| d15 | 2 | 2 |
| d16 / d17 | từ chối đúng / đúng | từ chối đúng / đúng |
