# Báo cáo Day 7 — Agentic RAG

**Học viên:** Phạm Đức Vinh · **MSSV:** 2A202603849 · **Lớp:** L3B · **Ngày:** 2026-11-16
**Repo:** `K5-L3B-DAY07-2A202603849-PhamDucVinh-RetrievalContext` · Cách chạy: [README.md](../../README.md) (phần "Bài làm")

## Dữ liệu và benchmark

- **Nguồn, quyền sử dụng, số trang và số chunk:** dùng lại corpus Day 6 — Thông tư 91/2026/TT-BTC của Bộ Tài chính
  (hóa đơn điện tử, chứng từ điện tử; ban hành 30/06/2026, hiệu lực 01/07/2026), tải từ vbpl.vn; văn bản quy phạm pháp luật
  công khai, không có dữ liệu cá nhân. PDF scan 97 trang, OCR Tesseract 5.4; index **trang 1–32** (thân văn bản Điều 1–25,
  32 trang nội dung, 72.408 ký tự). Phụ lục (trang 34–97) không index vì OCR nhiễu. Chunk lấy nguyên từ pgvector Day 6:
  **A = 235 chunk** (cửa sổ 360 ký tự, overlap 36, trong từng trang), **B = 275 chunk** (theo Điều/đoạn, tối đa 360 ký tự).
  Export ra `data/chunks_A.json`, `data/chunks_B.json` (`src/export_chunks.py`) cho BM25 và đánh giá.
- **Vector store, embedding model, phiên bản và số chiều:** PostgreSQL 16.16 + pgvector 0.8.7 (Docker, cổng local 55433),
  cosine, exact search (không ANN). Embedding `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` chạy local
  (sentence-transformers 6.3.0, torch 2.15.0+cpu), **384 chiều**, chuẩn hóa L2, query và tài liệu xử lý giống nhau, giới hạn
  128 token. Code kết nối copy nguyên từ Day 6 (`src/embeddings.py`, `src/store.py`, `src/models.py`). Kiểm tra: dense
  trên Day 7 tái lập đúng số Day 6 (A dev Hit@1 6/15, Hit@3 8/15; B có filter = C Day 6: 2/15, 8/15).
- **Agent model, cách chạy và phân chia dev/test:** GLM qua API z.ai (OpenAI-compatible, endpoint GLM Coding Plan
  `api.z.ai/api/coding/paas/v4`), tool calling gốc, `temperature=0`. Model thực tế API trả về trong mọi trace:
  **`glm-5.3-flash`** (ghi theo `response.model`). Vòng lặp: `run_agent` của `starter/agentic.py` giữ nguyên;
  controller tự viết `src/agent.py`; prompt `prompts/agent_system.md`. Benchmark **24 câu**: dev 15 có đáp án + 2 thiếu
  bằng chứng; test 5 có đáp án + 2 thiếu bằng chứng (`data/questions.json`, `data/cases.json`).
- **Cách xác định câu có/thiếu evidence và tiêu chí chấm:**
  - 20 câu có đáp án lấy từ benchmark Day 6 (chia theo Điều, test không trùng Điều với dev), mỗi câu có nguồn, trang và
    evidence chép nguyên văn OCR (kể cả lỗi dấu), đã kiểm evidence nằm đúng trang ở Day 6 và đối chiếu ảnh PDF.
  - 4 câu thiếu bằng chứng mới (d16 mức phạt tiền, d17 giá dịch vụ/hóa đơn, t06 thời hạn lưu trữ, t07 thuế suất GTGT %),
    gần chủ đề, dev và test khác chủ đề. Chứng minh vắng mặt bằng tìm từ khóa trên **toàn bộ** text trang 1–32
    (`src/search_corpus.py`), không dựa vào top-k; từ khóa và kết quả ghi trong `absence_reason`.
  - Hit (retrieval và context): cùng nguồn, trang gold thuộc `pages` của chunk, evidence nằm trọn trong chunk sau khi gộp
    khoảng trắng (giống `is_evidence_hit` Day 6). Không dùng `validate()` của `starter/baseline.py` vì so khớp không gộp
    khoảng trắng (báo trượt 17/20 câu do OCR xuống dòng giữa câu).
  - Evidence bị chunking cắt đôi (không chunk nào chứa trọn): A — d12, t04; B — d08. Giữ nguyên, tính là trượt.
  - Test dùng lại 5 câu test Day 6: Day 6 chốt chiến lược trước test, chạy test 1 lần, không chỉnh theo test. Rủi ro đã
    biết: t04 gần giống d01; kết quả test Day 6 đã được xem → mọi cải thiện ở Day 7 chỉ lấy lý do từ lỗi **dev**.

## Retrieval và thử nghiệm

Hit@1 / Evidence Hit@3: retrieval với **câu hỏi gốc**, filter chỉ khi câu hỏi có `filter` (`src/eval_retrieval.py`,
`results/retrieval/`). Context Evidence Rate: context cuối agent gửi model (`src/run_agent.py`, `src/eval_agent.py`).
N = 15 câu có đáp án (dev), 5 (test); câu thiếu bằng chứng không vào mẫu số. Chunk A cho mọi cấu hình agent.

| Cấu hình | Phương pháp, top-k, filter, rerank, context budget | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Thời gian / chi phí |
|---|---|---|---|---|---|---|---|
| Baseline `dense_A` | Dense pgvector cosine; top-k 3; filter `chapter` khi có; không rerank; budget 3000 ký tự; ≤ 3 search, truy vấn do model viết | Dense Day 6 làm mốc | dev | 6/15 (40%) | 8/15 (53%) | 12/15 (80%) | 52,6 s/câu; 63,8k + 29,4k token; retrieval 48–69 ms |
| Phương pháp 2 `bm25_A` | BM25 (k1 1,5, b 0,75, âm tiết lowercase); còn lại như baseline | Câu hỏi luật dùng từ khóa chính xác; MiniLM chỉ đọc 128 token | dev | 7/15 (47%) | 10/15 (67%) | 12/15 (80%) | 34,8 s/câu; 47,2k + 21,1k token; retrieval 2 ms |
| Phương pháp 3 `hybrid_A` | RRF (k = 60) dense + BM25-bigram, mỗi bên 20 candidate; còn lại như baseline | Gộp ưu điểm ngữ nghĩa + từ khóa | dev | 9/15 (60%) | 10/15 (67%) | 12/15 (80%) | 47,1 s/câu; 56,8k + 25,1k token; retrieval 58 ms |
| Cải thiện 1 `bm25_A_nb` | BM25 + mỗi hit ghép chunk trước/sau (±1, bỏ overlap); budget 6000 | Lỗi dev 1: evidence ở chunk liền kề / bị cắt đôi | dev | 10/15 (67%) | 14/15 (93%) | **15/15 (100%)** | 26,0 s/câu; 55,2k + 17,2k token; retrieval 3 ms |
| Cải thiện 2 `dense_A_oq` | Dense; lần search đầu = câu hỏi gốc (không gọi model), lượt sau model viết | Lỗi dev 2: truy vấn model viết lại kém hơn câu gốc cho dense | dev | 6/15 (40%)* | 8/15 (53%)* | 11/15 (73%) | 31,2 s/câu; 44,6k + 25,5k token |
| (Kết hợp) `hybrid_A_oq_nb` | Hybrid + cả hai thay đổi trên; budget 6000 | Hai lỗi độc lập → cộng dồn | dev | — | — | 15/15 (100%) | 24,4 s/câu; 55,3k + 18,3k token |
| **Cấu hình đã chọn** `bm25_A_nb` | như Cải thiện 1 | chốt trên dev | **test** | **4/5 (80%)** | **5/5 (100%)** | **5/5 (100%)** | 27,4 s/câu; 35,3k + 8,2k token; retrieval 3,8 ms |
| Baseline `dense_A` | như Baseline | — | test | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 26,2 s/câu; 26,8k + 7,7k token; retrieval 50 ms |

\* Retrieval với câu hỏi gốc của dense không đổi; thay đổi của Cải thiện 2 nằm ở pipeline agent: Hit@3 **lần search đầu**
của agent tăng 6/15 → 8/15. "—": hybrid kết hợp chỉ chạy agent, không chạy riêng retrieval.
Thời gian: s/câu là trung bình wall-clock mỗi câu của agent (gồm 2–4 lần gọi model); 3 cấu hình mỗi vòng chạy song song nên
chỉ so sánh thô. Chi phí tiền: embedding và DB local = 0; LLM qua GLM Coding Plan (gói tháng) → báo bằng token, không quy
ra tiền theo lượt. Context budget đo bằng **ký tự** (gồm tiêu đề `[id | nguồn | trang]` của mỗi đoạn).

**Một cấu hình vừa là phương pháp mới vừa là cải thiện?** Không: 3 phương pháp (dense, BM25, hybrid RRF) và 2 cải thiện
(ghép chunk liền kề; câu hỏi gốc ở lần search đầu) được mô tả và đo riêng. Hybrid kết hợp là thử thêm, không tính là cải thiện.

**Hai lỗi dev, nguyên nhân, cách thử** (`results/experiments.md`):
1. **Context có chunk liền kề nhưng thiếu chunk chứa evidence.** Ở cả 4 câu thiếu evidence còn hit được của vòng 1 (d11
   ở mọi cấu hình, d04 bm25, d06 hybrid, d07 dense), context cuối có chunk **ngay sát** chunk chứa evidence (vd. d04: có
   `p006:00`, evidence ở `p006:01`). Chunk A cắt cứng 360 ký tự nên câu luật bị cắt giữa chừng; d12 evidence bị chia qua
   2 chunk. Hệ quả: d06, d07 từ chối nhầm; d04 (bm25) trả lời thiếu ý. Thử: ghép ±1 chunk → **12 → 15/15**, đúng giả thuyết;
   d12 trở thành tìm được.
2. **Truy vấn model viết lại kém hơn câu gốc cho dense.** Hit@3 lần search đầu của dense_A 6/15, trong khi dense với câu
   gốc 8/15 — model hay rút câu hỏi thành chuỗi từ khóa, mất ngữ cảnh mà embedding cần. Thử: lần search đầu = câu gốc →
   Hit@3 lần đầu 6 → 8/15, token vào giảm 64k → 45k, từ chối nhầm 2 → 1; **nhưng Context Evidence Rate giảm 12 → 11/15**
   (mất d06). Kết luận: đúng một phần — câu gốc tốt hơn cho lần tìm đầu nhưng không sửa được lỗi chunk bị cắt.

**Lý do chọn cấu hình** (tiêu chí chốt trước khi chạy, `results/selection_criteria.md`; quyết định `results/selection.json`):
1) Context Evidence Rate: bm25_A_nb = hybrid_A_oq_nb = 15/15 → hòa. 2) Từ chối đúng 2/2, từ chối nhầm 0/15 cả hai → hòa.
3) Grounded answer chấm tay dev: lúc chốt (nhãn lượt 1) **1,80 so với 1,67** → chọn **bm25_A_nb**. Nhãn dev chính thức sau
đó (2,00 so với 1,93) không đổi lựa chọn. bm25_A_nb cũng đơn giản hơn (không cần embedding/DB khi chạy) và nhanh hơn ở
retrieval (3 ms so với ~60 ms).

## Agent và đánh giá

- **Tool, số lượt gọi, điều kiện dừng, cách chọn context và xử lý lỗi:**
  - 1 tool `search(query)` (native tool calling). Retriever cắm vào tool theo cấu hình; filter `chapter` lấy từ trường
    `filter` của câu hỏi (thông tin người dùng cung cấp trước), không suy ra từ gold.
  - Mỗi lượt: controller gọi model 1 lần với câu hỏi + các truy vấn đã dùng + context tích lũy mới nhất; model gọi `search`
    hoặc trả lời. Tối đa **3 search**; lượt cuối không đưa tool để buộc trả lời hoặc từ chối. Dừng khi model trả lời.
  - Context: `pack_context` của starter — khử trùng theo id, giữ đoạn từ lần search trước, cắt theo budget ký tự (3000;
    6000 khi ghép chunk liền kề vì mỗi đoạn dài gấp 2–3 lần). Nội dung tài liệu bọc trong `<context>` và prompt nói rõ
    là dữ liệu, không phải chỉ dẫn.
  - Citation: model ghi `[chunk-id]` sau mỗi ý; `[id1, id2]` được tách thành `[id1][id2]` (chỉ đổi định dạng). Citation
    không có trong context → starter chuyển thành từ chối. Từ chối: câu cố định "Không đủ bằng chứng…", không citation.
  - Lỗi API/DB → `status: "error"` kèm thông báo lỗi trong trace, không thay bằng kết quả giả. Đã gặp thật: DNS không
    phân giải `api.z.ai` khi chạy thử (2 câu ghi `error`, chạy lại sau khi mạng ổn). Các lần chạy dev/test được báo cáo:
    0 lỗi.

Nhãn chính thức (`starter/agent_metrics.py` → `results/agent/<cấu hình>/agent_metrics_<split>.json`):

| Cấu hình / split | Tool use | Số lượt gọi | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|---|
| bm25_A_nb / dev | 17/17 | search {1: 11, 2: 2, 3: 4}; 2,59 lần gọi model/câu | 0 / 0 / 15 → 2,00/2 | 30/30 | 15/15 | 2/2 | 0/15 |
| hybrid_A_oq_nb / dev | 17/17 | search {1: 7, 2: 6, 3: 4}; 2,82 lần gọi/câu | 0 / 1 / 14 → 1,93/2 | 30/30 | 15/15 | 2/2 | 0/15 |
| dense_A / test (baseline) | 7/7 | search {1: 1, 3: 6} | 3 / 1 / 1 → **0,60/2** | 2/4 | 2/2 | 2/2 | 3/5 |
| **bm25_A_nb / test (đã chọn)** | 7/7 | search {1: 1, 2: 2, 3: 4} | 0 / 0 / 5 → **2,00/2** | **8/8** | 5/5 | 2/2 | **0/5** |

Context chấm tay trên test (0 = không có evidence, 1 = có nhưng thiếu điều kiện/nguồn, 2 = đủ), 5 câu có đáp án:
dense_A **1 / 2 / 2**; bm25_A_nb **0 / 0 / 5**. Lý do từng câu: `results/agent/grades_test.md`.

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
| t01 (bm25_A_nb) | Có đáp án, diễn đạt lại | 3 search ("trụ sở chính căn hộ chung cư rủi ro cao", …, "Điều 7 rủi ro cao…"); context có Điều 7 khoản 3 và Điều 6 | "Có", trừ căn hộ được phép kinh doanh và trừ cá nhân kinh doanh; hệ quả: trong 01 ngày ra Thông báo giải trình, bổ sung `[p011:00][p008:04]` | Answer 2, citation 2/2, context 2 — đủ ý, hệ quả đúng văn bản |
| t01 (dense_A) | như trên | 3 search; context có p011:00 nhưng `p008:02` bị cắt đầu câu | Phần chính đúng; **hệ quả ngược văn bản** ("rủi ro cao thì chậm nhất ngày tiếp theo ra Thông báo chấp nhận") `[p001:04][p011:00][p008:02]` | Answer 1, citation 1/3 — p008:02 mất cụm "người nộp thuế **không thuộc** trường hợp" ở p008:00 |
| t02 (bm25_A_nb) | Có đáp án, trực tiếp | 2 search; khoản 3 Điều 13 trong context | "Không quá 150 tỷ đồng/năm" `[p025:04][p025:06]` | Answer 2, citation 2/2, context 2 |
| t03 (bm25_A_nb / dense_A) | Có đáp án | bm25: 2 search, có p031:01 · dense: 3 search, chỉ có ý gia hạn | bm25: 12 tháng (hoặc ≤ 12 theo đề nghị), gia hạn ≤ 12 tháng `[p031:01][p031:04]` · dense: từ chối | bm25 2 · dense 0 (từ chối nhầm, context 1) |
| t05 (bm25_A_nb / dense_A) | Có đáp án, trực tiếp | bm25: 1 search "hiệu lực thi hành" → p032:05 · dense: 3 search, không có Điều 25 | bm25: 01/7/2026 `[p032:05]` · dense: từ chối | bm25 2 · dense 0 (context 0) |
| t06 (bm25_A_nb) | Thiếu bằng chứng | 3 search về thời hạn lưu trữ; không đoạn nào có số năm | "Không đủ bằng chứng…" | Abstention đúng |
| t07 (bm25_A_nb) | Thiếu bằng chứng | 3 search về thuế suất dịch vụ hóa đơn | "Không đủ bằng chứng…" | Abstention đúng |

- **Đường dẫn trace, nhãn, lệnh chạy, thời gian và chi phí:** trace `results/agent/<cấu hình>/traces_{dev,test}.json`
  (mỗi câu: query_id, status, events search với query/filter/kết quả id-rank-score-trang/context/context_ids, answer,
  citations, final_context, model_calls với latency, model, token, raw answer), cấu hình `config.json`; nhãn
  `reviews_{dev,test}.json`; tổng hợp `agent_metrics_*.json`, `results/agent/summary_{dev,test}.json`; retrieval
  `results/retrieval/*.json` (top-10 + cờ hit từng câu). Lệnh: [README.md](../../README.md). Thời gian và token: bảng trên.
- **Kết quả trước/sau, ví dụ lỗi, đánh đổi và giới hạn:**
  - Trước/sau trên test: Context Evidence Rate 2/5 → 5/5, grounded 0,60 → 2,00, từ chối nhầm 3/5 → 0/5; đổi lại token
    +26% (34,5k → 43,5k) do mỗi đoạn context dài hơn. Thời gian/câu tương đương (~27 s), chủ yếu là thời gian sinh của model.
  - Ví dụ lỗi 1 (chunk cắt đảo nghĩa): dense_A t01 ở trên — lỗi nguy hiểm vì câu trả lời có citation "hợp lệ" (id có trong
    context) nhưng nội dung ngược văn bản; chỉ đọc đoạn trích mới phát hiện được.
  - Ví dụ lỗi 2 (trộn ngữ cảnh): hybrid_A_oq_nb d06 — ý chính đúng (03 ngày) nhưng ghép thủ tục giải trình khi đang sử
    dụng hóa đơn (p013:07, p014:02) vào thủ tục đăng ký; chấm 1. Đây là mặt trái của context dài.
  - Model đôi khi chèn kiến thức ngoài vào **truy vấn** ("tối thiểu 10 năm", "thuế suất 10%" ở t06/t07), nhưng không đưa
    vào câu trả lời; câu trả lời vẫn từ chối đúng.
  - Giới hạn: một văn bản, OCR lỗi dấu; test chỉ 5 câu có đáp án (1 câu = 20%) và 2 câu thiếu bằng chứng; t04 gần giống
    d01; model qua API không tất định dù `temperature=0` (chạy lại cùng câu cho số token khác); thời gian đo khi 3 cấu hình
    chạy song song; chỉ dùng chunk A cho agent (B có Hit@1 thấp ở Day 6 và GĐ1); không thử rerank; nhãn do một người
    chấm (xem mục Công cụ AI). Kết luận chỉ áp dụng cho corpus này.

## Thử thách nâng cao (nếu thực hiện)

Không thực hiện. Phụ lục Thông tư 91 (trang 34–97: biểu mẫu, bảng) OCR nhiễu nặng ở Day 6 nên không phù hợp làm tài liệu
≥ 100 trang có bảng, ảnh, biểu đồ đạt ngưỡng 90%.

