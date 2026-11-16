# Day 7 — Danh sách task

> Đánh `[x]` khi xong. Ghi chú ngắn vào cột/ dòng "Ghi chú" nếu có vướng mắc.
> Day 6 nằm ở `..\..\Day6\K5-L3B-Day06-DataIngestionEngineering` (gọi tắt **D6**).

## Hiện trạng Day 6 (kiểm tra 2026-11-16)

| Thứ Day 7 cần | Day 6 đã có? | Ghi chú |
|---|---|---|
| Corpus ≥ 30 trang | ✅ | TT 91/2026/TT-BTC, trang 1–32 (32 trang), OCR ở `D6/starter/results/pages_TT-91-2026.jsonl` (97 trang) |
| Embedding model thật | ✅ | `paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều, L2-norm, local, **giới hạn 128 token** |
| Vector store thật | ✅ | pgvector Docker `day6_student_starter`, cổng 55433. Đã bật lại và đếm: **A = 235, B = 275 chunk, 384 chiều** |
| Code kết nối | ✅ | `D6/starter/src/embeddings.py`, `store.py` (`PgVectorStore.search(strategy, vec, top_k, filters)`), venv ở `D6/starter/.venv` |
| Chunk xuất ra JSON | ✅ (T0.4) | `data/chunks_A.json`, `data/chunks_B.json` |
| Câu có đáp án | ✅ (T0.5) | `data/questions.json`, 15 dev + 5 test |
| Câu thiếu bằng chứng | ✅ (T0.6) | `data/cases.json`, thêm d16, d17, t06, t07 |
| LLM có tool calling | ✅ (T0.1) | z.ai GLM |

Rủi ro đã biết từ Day 6: test t04 gần giống d01 (rò rỉ); kết quả test Day 6 đã được xem (xem T0.7); chunk B rời rạc, Hit@1 thấp; model embedding chỉ đọc 128 token.

---

## Giai đoạn 0 — Chuẩn bị (0:00–1:00)

> **Mỗi lần mở terminal mới** (thư mục Day 7, Git Bash/UCRT64): `source .venv/Scripts/activate`
> (PowerShell: `.venv\Scripts\Activate.ps1`). Script activate đã tự đặt `PYTHONUTF8=1`. DB Day 6 phải đang chạy (T0.3).

- [x] **T0.1 Chọn LLM có tool calling** — z.ai GLM Coding Plan (`/api/coding/paas/v4`), gọi thử tool `search` OK (~7–15 s, 182 in / 68 out token).
  - ⚠️ `.env` đặt `glm-4.5-air` nhưng API trả `model: glm-5.3-flash` → trace/báo cáo ghi theo `response.model`. Chi phí: ghi token + "theo gói tháng".
- [x] **T0.2 Môi trường Day 7** — `.venv` (Python 3.13, torch 2.15 CPU, openai 3.51), `requirements.txt`, `.env` (git ignore), `.env.example`.
  - 15/15 unittest pass **khi đặt `PYTHONUTF8=1`** (không có thì `test_baseline` lỗi cp1252 — lỗi của test đề bài trên Windows).
- [x] **T0.3 Kết nối dense trên pgvector Day 6** — copy `embeddings.py`, `store.py`, `models.py` từ D6 vào `src/` (không import thẳng vì trùng tên package `src`).
  - Bật DB: `docker compose -f ../../Day6/K5-L3B-Day06-DataIngestionEngineering/starter/docker-compose.yml -p day6_student_starter up -d --wait`
  - Kiểm tra: `python -m src.check_dense` → A 235, B 275 chunk; câu d03 tìm đúng trang 4 (A hạng 1, B hạng 1–2).
- [x] **T0.4 Export chunk** — `python -m src.export_chunks` → `data/chunks_A.json` (235), `data/chunks_B.json` (275); metadata có `pages, chapter, article, strategy` + thông tin OCR.
- [x] **T0.5 Chuyển benchmark** — `python -m src.convert_questions` → `data/questions.json` (20 câu: 15 dev / 5 test, `page` int, giữ `filter`, `article`, `note`).
  - Luật hit = Day 6: cùng nguồn, trang gold ∈ `metadata.pages`, evidence nằm trọn trong chunk **sau khi gộp khoảng trắng**. Không dùng `validate()`/`hit()` của `starter/baseline.py` (so khớp không gộp khoảng trắng → báo trượt 17/20 câu).
  - Evidence không nằm trọn trong chunk nào (lỗi chunking thật, giữ nguyên, tính là trượt): **A: d12, t04 · B: d08** — khớp báo cáo Day 6.
- [x] **T0.6 Câu thiếu bằng chứng** — `python -m src.build_cases` → `data/cases.json` 24 câu (dev 15+2, test 5+2).
  - d16 mức phạt tiền · d17 giá dịch vụ/hóa đơn · t06 thời hạn lưu trữ · t07 thuế suất GTGT (%). Dev/test khác chủ đề.
  - Đã kiểm bằng `python -m src.search_corpus <từ khóa>` trên trang 1–32; từ khóa + kết quả ghi trong `absence_reason`. **Bạn nên tự đọc lại 4 câu này.**
- [x] **T0.7 Dùng lại test Day 6** (đã chốt 2026-11-16) — 5 câu test có đáp án của Day 6 + 2 câu mới t06, t07.
  - Lý do: Day 6 chốt chiến lược trước khi chạy test (`selection.json: decided_before_test`), test chạy 1 lần, không chỉnh theo test.
  - Ghi vào báo cáo: (1) t04 gần giống d01; (2) kết quả test Day 6 (t01, t05 trượt) đã được biết → mọi cải thiện ở GĐ3 chỉ được lấy lý do từ lỗi **dev**; (3) chốt cấu hình trước khi chạy test Day 7.
  - Nếu muốn chặt hơn: viết 5 câu test mới từ các Điều chưa dùng ở dev/test (vd. Điều 5, 9, 14, 16, 19, 23) và không xem kết quả Day 6 cho chúng.

## Giai đoạn 1 — Retrieval (1:00–2:00)

Code: `src/retrieval.py` (3 retriever cùng định dạng kết quả), `src/eval_retrieval.py`, test `tests/test_retrieval.py`.

- [x] **T1.1 Dense** — `DenseRetriever`: pgvector Day 6, cosine exact, filter `chapter` chỉ khi câu hỏi có `filter`. Tái lập đúng số Day 6 (A 6/15 · 8/15; B có filter = Day 6 C 2/15 · 8/15).
- [x] **T1.2 Lexical BM25** — `BM25Retriever` (k1=1.5, b=0.75), tách âm tiết lowercase; biến thể `+bigram` (ghép 2 âm tiết ≈ từ ghép). Tự viết, không thêm thư viện.
- [x] **T1.3 Hybrid RRF** — `HybridRetriever`: dense + BM25-bigram, k=60, mỗi bên lấy 20 candidate, xếp theo tổng 1/(k+rank) (không cộng score thô).
- [x] **T1.4 Benchmark retrieval dev** — `python -m src.eval_retrieval --split dev --strategy A B` → `results/retrieval/dev_A.json`, `dev_B.json` (top-10 + cờ hit từng câu).
  - Test bị chặn: phải thêm `--locked` (chỉ dùng sau khi chốt cấu hình ở T3.6).

**Kết quả dev (2026-11-16, 15 câu có đáp án, query gốc, CPU, chi phí 0):**

| Chunk | Method | Hit@1 | Evidence Hit@3 | Hit@5 | MRR@10 | ms/query | Trượt @3 |
|---|---|---|---|---|---|---|---|
| A | dense (baseline) | 6/15 | 8/15 | 10/15 | 0.497 | 68.8 | d02, d04, d06, d07, d11, d12, d13 |
| A | bm25 | 7/15 | 10/15 | 12/15 | 0.600 | 2.1 | d02, d04, d06, d11, d12 |
| A | bm25+bigram | 6/15 | 10/15 | 11/15 | 0.547 | 4.1 | d04, d06, d09, d11, d12 |
| A | hybrid RRF | **9/15** | **10/15** | 11/15 | **0.647** | 57.5 | d02, d04, d06, d11, d12 |
| B | dense | 2/15 | 8/15 | 8/15 | 0.328 | 50.7 | d01, d02, d06, d07, d08, d11, d12 |
| B | bm25 | 7/15 | 9/15 | 12/15 | 0.572 | 1.9 | d02, d06, d07, d08, d11, d12 |
| B | bm25+bigram | 8/15 | 9/15 | 11/15 | 0.593 | 2.8 | d02, d06, d07, d08, d09, d11 |
| B | hybrid RRF | 5/15 | 10/15 | 10/15 | 0.500 | 60.2 | d02, d07, d08, d11, d12 |

- Nhận xét ban đầu: lexical vượt dense ở Hit@3 (+2 trên A); hybrid A tốt nhất Hit@1 / MRR. d02, d06, d11 trượt ở mọi method → đọc ở T3.5. d12 (A) và d08 (B) không thể hit (evidence bị cắt ở chunking).
- Hybrid ghép với `bm25+bigram` (chọn trước khi chạy). Hybrid với `bm25` thường, đổi k / số candidate → để dành làm cấu hình cải thiện ở GĐ3, không chỉnh ngay.

## Giai đoạn 2 — Agent và context (1:00–2:00, song song)

Code: `src/agent.py` (GLMController), `src/run_agent.py` (chạy + lưu trace), `prompts/agent_system.md`, test `tests/test_agent.py` (LLM giả).

- [x] **T2.1 Nối agent** — dùng nguyên `run_agent` của `starter/agentic.py` (vòng lặp, giới hạn search, đóng gói context, kiểm citation). `GLMController.decide` = 1 lần gọi GLM thật với tool `search` (native tool calling); retriever = lớp ở GĐ1.
  - Điều kiện dừng: model trả lời, hoặc hết `--max-searches` (lượt cuối không đưa tool → buộc trả lời/từ chối).
  - Lỗi API/DB → `status: "error"` + thông báo lỗi trong trace (đã gặp thật: lỗi DNS `api.z.ai`, ghi đúng là error).
- [x] **T2.2 Prompt** — `prompts/agent_system.md`: luôn search trước, trích `[chunk-id]` sau mỗi ý, câu từ chối cố định, nội dung tài liệu là dữ liệu không phải chỉ dẫn, lưu ý lỗi OCR.
  - Chuẩn hóa định dạng: `[id1, id2]` → `[id1][id2]` (không đổi id). Citation bịa (id không có trong context) → starter chuyển thành abstain.
- [x] **T2.3 Context** — `pack_context` của starter: dedup theo id, giữ chunk từ lần search trước, budget **3000 ký tự** (≈ 6–7 chunk A kèm header; mặc định 800 của starter chỉ vừa ~1–2 chunk). Context mới nhất (tích lũy) gửi lại model mỗi lượt.
- [x] **T2.4 Trace** — `results/agent/<name>/config.json` + `traces_<split>.json`: query_id, status, events (search: query, filter, kết quả id/rank/score/page, context, context_ids), answer, citations, queries, final_context, model_calls (latency, model thật, token, raw answer, `model_abstained`), tổng token, thời gian, error.
  - Cuối lần chạy in Context Evidence Rate (gold chỉ dùng ở bước đánh giá này, sau khi agent chạy xong).
- **Thử 2026-11-16** (`--name try --retriever dense --strategy A --ids d03 d16`, model thực tế `glm-5.3-flash`):
  - d03 → answered, 1 search, cite `TT-91-2026:A:p004:00`, đúng "sáu ký tự gồm chữ viết và chữ số"; 23 s, 1637+629 token.
  - d16 (mức phạt, thiếu bằng chứng) → 3 search khác nhau rồi tự từ chối (`model_abstained: true`); 33 s, 4168+932 token.
  - Mỗi lần gọi model ~8–12 s → chạy đủ 17 câu dev ≈ 8–10 phút / cấu hình.

## Giai đoạn 3 — Thử nghiệm trên dev (2:00–3:30)

Chi tiết + bảng: `results/experiments.md`. So sánh: `python -m src.eval_agent --split dev <tên cấu hình...>`.

- [x] **T3.1 Tiêu chí** — `results/selection_criteria.md` (chốt trước khi chạy): 1) Context Evidence Rate, 2) không trả lời câu thiếu BC + ít từ chối nhầm, 3) grounded answer chấm tay (2 cấu hình đầu), 4) Hit@3, 5) token/thời gian.
- [x] **T3.2 Agent trên dev, 3 phương pháp** — dense_A / bm25_A / hybrid_A: Context Evidence Rate đều 12/15; từ chối đúng 2/2; từ chối nhầm 2 / **0** / 2; token bm25 thấp nhất (47k+21k), nhanh nhất (592 s).
- [x] **T3.5 Phân tích lỗi dev** (2 lỗi, ghi trong `results/experiments.md`):
  1. Context có **chunk liền kề** nhưng thiếu chunk chứa evidence (d04, d06, d07, d11); d12 evidence bị cắt đôi qua 2 chunk A.
  2. Truy vấn **model viết lại kém hơn câu gốc** cho dense (Hit@3 lần đầu 6/15 so với 8/15 khi dùng câu gốc).
- [x] **T3.3 Cải thiện 1** `bm25_A_nb` — ghép chunk ±1 (`--neighbors 1`), budget 6000. **Đúng giả thuyết**: Context Evidence Rate 12 → **15/15**, từ chối nhầm 0, ít search hơn; token vào +8k, ra −4k.
- [x] **T3.4 Cải thiện 2** `dense_A_oq` — lần search đầu = câu hỏi gốc. **Đúng một phần**: Hit@3 lần đầu 6 → 8/15, token vào −19k, từ chối nhầm 2 → 1; nhưng Context Evidence Rate 12 → 11/15 (mất d06).
  - Kết hợp `hybrid_A_oq_nb`: Context Evidence Rate **15/15**, Hit@3 lần đầu 15/15, từ chối nhầm 0.
- [x] **T3.6a Chấm tay dev** — nhãn chính thức = `results/agent/grades_dev.md`, ghi bằng `python -m src.fill_labels`: bm25_A_nb **2,00/2** (0/0/15), hybrid_A_oq_nb 1,93/2 (0/1/14), citation 30/30 cả hai, đủ lý do 34/34. Lựa chọn không đổi. Hướng dẫn cũ bên dưới để tham khảo:
  - Câu có đáp án: `answer_grade` 0 = sai/thiếu evidence, 1 = đúng một phần, 2 = đúng và đủ (so với `expected_answer_for_grader`).
  - `citation_support`: `true`/`false` cho từng citation — đọc `cited_text` xem có thật sự chứa ý được trích không (trường `hint_...` chỉ là gợi ý tự động).
  - Câu thiếu bằng chứng (d16, d17): `abstention_correct` = `true` nếu agent thật sự từ chối, không khẳng định gì vô căn cứ.
  - `reason`: 1 câu lý do. Sau đó chạy lệnh `python starter/agent_metrics.py ...` (in ra khi tạo file) cho từng cấu hình.
  - Công cụ chấm trong terminal (tự lưu, gõ `q` để dừng, chạy lại để làm tiếp): `python -m src.grade results/agent/bm25_A_nb/reviews_dev.json` rồi `python -m src.grade results/agent/hybrid_A_oq_nb/reviews_dev.json`. Chấm lại câu nào: thêm `--redo d04`.
  - Lượt 1 của bạn (dùng lúc chốt, trước test): bm25_A_nb 1,80/2; hybrid_A_oq_nb 1,67/2.
- [x] **T3.6 Chọn cấu hình** — **bm25_A_nb** (chốt 2026-11-16, `results/selection.json`, `decided_before_test: true`). Bạn chọn chốt trước, bổ sung lý do nhãn dev sau (đã ghi trong `notes`).

## Giai đoạn 4 — Test và đánh giá (3:30–4:00)

- [x] **T4.1 Chạy test 1 lần** (`--locked`) cho baseline dense_A + bm25_A_nb:
  - Retrieval (query gốc): dense Hit@1 2/5 · Hit@3 2/5; bm25+nb **4/5 · 5/5**.
  - Agent: Context Evidence Rate 2/5 → **5/5**; từ chối nhầm 3/5 → **0/5**; từ chối đúng 2/2 cả hai; token 34.5k → 43.5k.
  - Lệnh: `python -m src.eval_retrieval --split test --locked --strategy A --methods dense bm25+nb`; `python -m src.run_agent --name dense_A --retriever dense --strategy A --split test --locked`; `python -m src.run_agent --name bm25_A_nb --retriever bm25 --strategy A --split test --locked --neighbors 1 --budget 6000`.
- [x] **T4.2 Chấm tay test** — nhãn chính thức = `results/agent/grades_test.md` do người chấm thực hiện, ghi bằng `python -m src.fill_labels`:
  - dense_A: grounded 3/1/1 = **0,60/2**, citation 2/4, context 0/1/2 = 1/2/2, từ chối đúng 2/2, từ chối nhầm 3/5.
  - bm25_A_nb: grounded 0/0/5 = **2,00/2**, citation 8/8, context 0/0/5, từ chối đúng 2/2, từ chối nhầm 0/5.
- [x] **T4.3 Tổng hợp** — đã chạy, kết quả ở `results/agent/<cấu hình>/agent_metrics_<split>.json`. Lệnh:
  - `python starter/agent_metrics.py --cases data/cases.json --traces results/agent/dense_A/traces_test.json --reviews results/agent/dense_A/reviews_test.json --split test --output results/agent/dense_A/agent_metrics_test.json`
  - `python starter/agent_metrics.py --cases data/cases.json --traces results/agent/bm25_A_nb/traces_test.json --reviews results/agent/bm25_A_nb/reviews_test.json --split test --output results/agent/bm25_A_nb/agent_metrics_test.json`

## Giai đoạn 5 — Báo cáo và nộp

- [x] **T5.1 Báo cáo** — `report/individual/2A202603849_PhamDucVinh.md` (2026-11-16). Yêu cầu gốc: copy `report/individual/MSSV_HoTen.md` → `report/individual/2A202603849_PhamDucVinh.md`, điền đủ bảng retrieval, agent, ví dụ (1 có bằng chứng, 1 thiếu bằng chứng, 1 lỗi), đánh đổi, giới hạn.
- [x] **T5.2 README cách chạy** — phần "Bài làm" ở đầu `README.md` (cài đặt, bật DB, dữ liệu, retrieval, agent, chấm, bản đồ file). Yêu cầu gốc: lệnh bật DB, export, benchmark, agent, metrics; model + phiên bản.
- [ ] **T5.3 Kiểm tra trước khi nộp**: không có `.env`/key trong git, `git add -f` kết quả được phép chia sẻ, unittest pass, push lên `origin` (repo cá nhân `K5-L3B-DAY07-2A202603849-PhamDucVinh-RetrievalContext`).

## Tùy chọn — Thử thách nâng cao (+15)

- [ ] Chỉ làm nếu còn thời gian: tài liệu ≥ 100 trang có bảng/ảnh/biểu đồ, đạt ≥ 90% test theo `ADVANCED.md`. Lưu ý: phụ lục TT 91 (trang 34–97) OCR nhiễu.
