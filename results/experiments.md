# Nhật ký thử nghiệm (dev)

## Vòng 1 — 3 phương pháp (agent, chunk A, top-k 3, budget 3000 ký tự, max 3 search, truy vấn do model viết)

| Cấu hình | Context Evidence Rate | Hit@3 lần search đầu | Answered / Abstain | Từ chối nhầm | Token in+out | Thời gian |
|---|---|---|---|---|---|---|
| dense_A (baseline) | 12/15 | 6/15 | 13 / 4 | 2/15 (d07, d12) | 63759+29362 | 894 s |
| bm25_A | 12/15 | 10/15 | 15 / 2 | 0/15 | 47234+21114 | 592 s |
| hybrid_A | 12/15 | 10/15 | 13 / 4 | 2/15 (d06, d12) | 56784+25119 | 801 s |

Cả 3 từ chối đúng 2/2 câu thiếu bằng chứng (d16, d17). 3 cấu hình chạy song song → thời gian là wall-clock từng câu, có tranh chấp API.

## Phân tích lỗi dev (đọc trace)

1. **Chunk liền kề** — ở cả 4 câu thiếu evidence còn hit được (d11 mọi cấu hình, d04 bm25, d06 hybrid, d07 dense),
   context cuối **có chunk ngay sát** chunk chứa evidence (vd. d04: có `p006:00`, evidence ở `p006:01`). Chunk A cắt cứng
   360 ký tự nên câu luật bị cắt giữa chừng. d12: evidence bị chia qua 2 chunk A → không chunk nào chứa trọn.
   Hệ quả: d04 (bm25) trả lời thiếu ý vị trí tiếng Anh; d06, d07 từ chối nhầm dù đã tìm đúng chỗ.
2. **Truy vấn model viết lại kém hơn câu gốc cho dense** — Hit@3 lần search đầu của dense_A = 6/15, trong khi dense với
   câu hỏi gốc (GĐ1) = 8/15. Model hay rút ngắn câu hỏi thành chuỗi từ khóa, mất ngữ cảnh mà embedding cần.

## Vòng 2 — cải thiện (giả thuyết ghi TRƯỚC khi chạy, 2026-11-16)

| Tên | Thay đổi so với gốc | Giả thuyết | Kỳ vọng đo được |
|---|---|---|---|
| **Cải thiện 1** `bm25_A_nb` | bm25_A + mỗi hit ghép thêm chunk trước/sau (±1, bỏ phần overlap), budget 3000 → 6000 ký tự để vẫn chứa ~2 lượt search | Lỗi #1: evidence nằm ở chunk liền kề / bị cắt đôi | Context Evidence Rate > 12/15 (d04, d11, d12 vào context); không tăng từ chối nhầm; token tăng |
| **Cải thiện 2** `dense_A_oq` | dense_A + lần search đầu dùng nguyên câu hỏi gốc (không gọi model); lượt sau model tự viết | Lỗi #2: truy vấn viết lại làm dense kém | Hit@3 lần search đầu 6 → ~8/15; ít search hơn; token giảm (bớt 1 lần gọi model/câu) |
| Kết hợp `hybrid_A_oq_nb` | hybrid_A + cả hai thay đổi trên (budget 6000) | Hai lỗi độc lập → cộng dồn | Context Evidence Rate ≥ cải thiện 1; Hit@3 lần đầu ≥ hybrid_A |

## Vòng 2 — kết quả (dev, 2026-11-16)

| Cấu hình | Context Evidence Rate | Hit@3 lần search đầu | Answered / Abstain | Từ chối đúng | Từ chối nhầm | Số lần search {n: số câu} | Token in+out | Thời gian |
|---|---|---|---|---|---|---|---|---|
| dense_A (baseline) | 12/15 | 6/15 | 13 / 4 | 2/2 | 2 (d07, d12) | {1: 2, 2: 5, 3: 10} | 63759+29362 | 894 s |
| bm25_A | 12/15 | 10/15 | 15 / 2 | 2/2 | 0 | {1: 8, 2: 3, 3: 6} | 47234+21114 | 592 s |
| hybrid_A | 12/15 | 10/15 | 13 / 4 | 2/2 | 2 (d06, d12) | {1: 6, 2: 2, 3: 9} | 56784+25119 | 801 s |
| **Cải thiện 1** bm25_A_nb | **15/15** | 14/15 | 15 / 2 | 2/2 | 0 | {1: 11, 2: 2, 3: 4} | 55231+17166 | 441 s |
| **Cải thiện 2** dense_A_oq | 11/15 | 8/15 | 14 / 3 | 2/2 | 1 (d12) | {1: 4, 2: 6, 3: 7} | 44584+25530 | 531 s |
| Kết hợp hybrid_A_oq_nb | **15/15** | **15/15** | 15 / 2 | 2/2 | 0 | {1: 7, 2: 6, 3: 4} | 55323+18263 | 414 s |

Thời gian: 3 cấu hình mỗi vòng chạy song song (wall-clock, có tranh chấp API) → chỉ so sánh thô.

**Cải thiện 1 — giả thuyết ĐÚNG.** Context Evidence Rate 12 → 15/15: d04, d11, d12 đều vào context (d12 nhờ cửa sổ
nối 2 nửa evidence). Ít lượt search hơn (11/17 câu chỉ cần 1 lần), token đầu ra giảm (21k → 17k), token đầu vào tăng
(47k → 55k) do mỗi đoạn dài gấp ~2–3 lần. Không tăng từ chối nhầm.

**Cải thiện 2 — giả thuyết đúng một phần.** Hit@3 lần search đầu tăng đúng như dự đoán (6 → 8/15), token đầu vào giảm
(64k → 45k, bớt 1 lần gọi model/câu), từ chối nhầm 2 → 1. NHƯNG Context Evidence Rate giảm 12 → 11/15: mất d06 (lần
đầu trúng chunk liền kề, các lượt sau không tìm thêm được). Kết luận: câu gốc tốt hơn cho lần tìm đầu, nhưng không sửa
được lỗi chunk bị cắt — lỗi đó mới là nguyên nhân chính.

**Kết hợp** — bằng cải thiện 1 ở Context Evidence Rate (15/15), Hit@3 lần đầu cao nhất (15/15).

## Áp tiêu chí (`selection_criteria.md`)

1. Context Evidence Rate: **bm25_A_nb = hybrid_A_oq_nb = 15/15** → hòa.
2. Trả lời sai loại: cả hai từ chối đúng 2/2, từ chối nhầm 0/15 → hòa.
3. Grounded answer chấm tay trên dev — **chờ người chấm** (`results/agent/{bm25_A_nb,hybrid_A_oq_nb}/reviews_dev.json`).
   9/17 câu khác citation giữa 2 cấu hình: d02, d04, d05, d06, d07, d09, d10, d11, d15.
4. (nếu vẫn hòa) Evidence Hit@3 retrieval GĐ1: bm25 A 10/15 = hybrid A 10/15.
5. (nếu vẫn hòa) Token: bm25_A_nb 72.4k < hybrid_A_oq_nb 73.6k; bm25 không cần DB/embedding khi chạy.

## Chốt cấu hình (2026-11-16, trước khi chạy test)

Chọn **bm25_A_nb** (`results/selection.json`): hòa hybrid_A_oq_nb ở tiêu chí 1–2, thắng tiêu chí 3 (grounded answer
dev 1,80 so với 1,67, chấm tay). Baseline để so sánh trên test: dense_A. Retrieval dev của pipeline đã chọn
(`bm25+neighbors(±1)`, query gốc): Hit@1 10/15, Evidence Hit@3 14/15, MRR 0,802 (dense: 6/15, 8/15, 0,497).

## Test (chạy 1 lần với `--locked`, sau khi chốt)

Retrieval (query gốc, `results/retrieval/test_A_dense_bm25-nb.json`):

| Method | Hit@1 | Evidence Hit@3 | Hit@5 | MRR@10 | Trượt @3 |
|---|---|---|---|---|---|
| dense (baseline) | 2/5 | 2/5 | 3/5 | 0.472 | t01, t04, t05 |
| bm25+neighbors(±1) (đã chọn) | 4/5 | 5/5 | 5/5 | 0.900 | — |

Agent (`results/agent/{dense_A,bm25_A_nb}/traces_test.json`):

| Cấu hình | Context Evidence Rate | Answered / Abstain / Error | Từ chối đúng (thiếu BC) | Từ chối nhầm | Câu trả lời có citation | Token in+out | Thời gian |
|---|---|---|---|---|---|---|---|
| dense_A (baseline) | 2/5 | 2 / 5 / 0 | 2/2 | 3/5 (t03, t04, t05) | 2/2 | 26814+7678 | 184 s |
| **bm25_A_nb (đã chọn)** | **5/5** | 5 / 2 / 0 | 2/2 | **0/5** | 5/5 | 35271+8237 | 192 s |

Chấm tay test (grounded, citation, abstention, context 0/1/2): **chờ người chấm** —
`results/agent/{dense_A,bm25_A_nb}/reviews_test.json`.
Giới hạn: test chỉ 5 câu có đáp án (1 câu = 20%); t04 gần giống d01; kết quả test Day 6 đã được xem trước (xem task T0.7).

## Nhãn chính thức (2026-11-16)

Nguồn gốc: AI (Claude) chấm nháp sau khi đọc từng câu trả lời, đoạn trích và context; người chấm (Phạm Đức Vinh) xem
`results/agent/grades_{dev,test}.md` và chấp nhận làm nhãn chính thức; ghi vào `reviews_*.json` bằng `python -m src.fill_labels`,
tổng hợp bằng `starter/agent_metrics.py` → `results/agent/<cấu hình>/agent_metrics_<split>.json`.

| Cấu hình / split | Grounded 0/1/2 (trung bình /2) | Citation hỗ trợ | Câu trả lời có citation | Từ chối đúng | Từ chối nhầm | Tool use | Context 0/1/2 |
|---|---|---|---|---|---|---|---|
| bm25_A_nb / dev | 0/0/15 (2,00) | 30/30 | 15/15 | 2/2 | 0/15 | 17/17 | — |
| hybrid_A_oq_nb / dev | 0/1/14 (1,93) | 30/30 | 15/15 | 2/2 | 0/15 | 17/17 | — |
| dense_A / test (baseline) | 3/1/1 (0,60) | 2/4 | 2/2 | 2/2 | 3/5 | 7/7 | 1/2/2 |
| **bm25_A_nb / test (đã chọn)** | **0/0/5 (2,00)** | **8/8** | 5/5 | 2/2 | **0/5** | 7/7 | **0/0/5** |

Lúc chốt cấu hình (trước test) dùng nhãn dev lượt 1 của người chấm (1,80 so với 1,67); nhãn chính thức sau đó
(2,00 so với 1,93) không đổi lựa chọn.

Ví dụ lỗi tiêu biểu:
- **dense_A t01 (test)** — chunk bị cắt đảo nghĩa: p008:02 mất cụm "người nộp thuế không thuộc trường hợp" (nằm ở p008:00),
  agent khẳng định người rủi ro cao được chấp nhận ngay — ngược văn bản. bm25_A_nb (có chunk liền kề) trả lời đúng.
- **hybrid_A_oq_nb d06 (dev)** — trộn ngữ cảnh: ý chính đúng nhưng ghép thủ tục giải trình khi đang sử dụng hóa đơn
  (p013:07, p014:02) vào thủ tục đăng ký.
