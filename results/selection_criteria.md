# Tiêu chí chọn cấu hình (chốt 2026-11-16, TRƯỚC khi chạy agent trên dev)

Áp dụng cho mọi cấu hình chạy trên **dev** (17 câu: 15 có đáp án, 2 thiếu bằng chứng). Test chỉ chạy sau khi đã chọn
và ghi `results/selection.json`.

Xếp theo thứ tự, chỉ xét tiêu chí sau khi tiêu chí trước hòa (chênh ≤ 1 câu):

1. **Context Evidence Rate (dev)** — số câu có đáp án mà context cuối gửi model chứa evidence hợp lệ / 15.
   Tự động, cùng luật hit với retrieval (Day 6 `is_evidence_hit`).
2. **Không trả lời sai loại** — (a) không câu thiếu bằng chứng nào bị trả lời; (b) ít câu có đáp án bị từ chối nhầm.
   Tính theo status, người chấm xác nhận lại khi chấm tay.
3. **Grounded answer trung bình /2 (dev, chấm tay)** — chỉ chấm cho 2 cấu hình đứng đầu sau bước 1–2.
4. **Evidence Hit@3 retrieval (dev)** — từ `results/retrieval/dev_A.json` / `dev_B.json`.
5. **Chi phí và thời gian** — tổng token (in + out) và thời gian chạy dev; ít hơn thì tốt hơn.

Cố định cho mọi so sánh: cùng `data/cases.json`, cùng chunk/index, cùng prompt `prompts/agent_system.md`, cùng
model endpoint (z.ai, `temperature=0`), query gốc của câu hỏi, filter chỉ dùng khi câu hỏi có `filter`.

Giới hạn đã biết: model qua API không tất định hoàn toàn dù `temperature=0` → chênh 1 câu chưa đủ kết luận.
Lỗi API (status `error`) không tính vào chất lượng; nếu có, chạy lại riêng câu đó và ghi chú.
