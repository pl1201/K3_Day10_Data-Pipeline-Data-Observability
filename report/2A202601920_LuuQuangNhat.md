# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                          |
| ------------------ | ---------------------------------------------------------------------------------- |
| Họ và tên       | Lưu Quang Nhật                                                                   |
| MSSV               | 2A202601920                                                                        |
| Khóa/Lớp         | K3                                                                                 |
| Tên nhóm         | C2-2                                                              |
| Vai trò chính    | Thành viên 4 — Integration & Pipeline Fix (`src/pipelines/phase1.py`, `pyproject.toml`) |
| Repository         | https://github.com/pl1201/K3_Day10_Data-Pipeline-Data-Observability               |
| Ngày hoàn thành | 2026-08-06                                                                         |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable                  | File/hàm phụ trách                      | Input nhận vào                                               | Output bàn giao                                                  | Trạng thái |
| ----------------------------------- | ---------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------- | ----------- |
| Fix môi trường Python & deps        | `pyproject.toml`                        | Lỗi `requires-python` và `great-expectations` version sai   | Cả nhóm cài được môi trường, `pip install -e .` thành công       | Hoàn thành |
| Implement baseline pipeline (phần RAG/index) | `src/pipelines/phase1.py` → `main()` | Settings, raw records, clean DataFrame từ các thành viên khác | `phase1.py` có thể gọi được `LocalEmbeddingIndex.build()`, `evaluate_pipeline()`, `build_agent()` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                                              | Thành viên/module được hỗ trợ | Kết quả                                                                                       |
| ------------------------------------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------- |
| Đọc và hiểu `corruption.py` của Kim Mạnh Hưng          | Toàn nhóm (review)            | Xác nhận `df.copy()` đảm bảo baseline không bị mutate; log có đủ `before/after` để repair   |
| Phân tích luồng corruption → quality signal → metric   | Thành viên 3 (Observability)  | Giải thích tại sao `drop_record` ảnh hưởng `retrieval_hit_rate` nhiều nhất trong comparison  |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện                          | File/hàm/artifact liên quan              | Kết quả bàn giao                                          | Cách xác minh                                                |
| ----------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------- |
| Fix `requires-python` và `great-expectations`   | `pyproject.toml`                          | Toàn nhóm cài được môi trường trên Python 3.14            | `pip install -e .` chạy thành công không còn error           |
| Implement `main()` trong `phase1.py`            | `src/pipelines/phase1.py`                | Orchestrate 10 bước raw→clean→index→eval→report          | `git log --oneline src/pipelines/phase1.py` → commit `77ec22e update_role_4` |
| Tích hợp `LocalEmbeddingIndex.build()` vào pipeline | `src/pipelines/phase1.py` bước 5    | Collection `papers-baseline` được tạo đúng               | `data/embeddings/papers_embeddings.json` tồn tại, `collection_name: papers-baseline` |
| Tích hợp `evaluate_pipeline()` và demo agent   | `src/pipelines/phase1.py` bước 7, 10    | `baseline_metrics.json`, `baseline_answers.json`, `agent_demo_answers.json` | `cat data/results/baseline_metrics.json` |

**Output cụ thể:** Commit `77ec22e` (author: nhatngoonslaof) thêm 136 dòng vào `phase1.py`, biến file chỉ có `raise NotImplementedError` thành pipeline 10 bước hoàn chỉnh. Kết quả: `baseline_metrics.json` với `retrieval_hit_rate=1.00`, `mean_token_f1=0.42`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

`phase1.py` ban đầu chỉ có `raise NotImplementedError`. Pipeline cần một điểm điều phối (orchestrator) kết nối output của tất cả các thành viên (raw records từ TV1, clean data từ TV2, quality/report từ TV3, corruption từ TV4) thành một luồng chạy được end-to-end. Ngoài ra, môi trường Python 3.14 không tương thích với `pyproject.toml` ban đầu, cần fix trước khi cả nhóm cài được dependencies.

### Cách triển khai

**Fix `pyproject.toml`:** Sửa 2 điểm:
- `requires-python = ">=3.11,<3.14"` → `">=3.11,<3.15"` để cho phép Python 3.14
- `great-expectations>=1.16.1` → `>=0.16.1` vì phiên bản 1.16.1 không tồn tại

**Implement `phase1.py`:** Hàm `main()` orchestrate 10 bước theo thứ tự dependency:

1. `load_settings()` — đọc `.env` và config paths
2. `fetch_source_records()` hoặc `load_raw_records()` — có guard `refresh_source` để tránh gọi lại API khi không cần
3. `build_clean_dataframe()` — nhận records từ TV1, gọi module của TV2
4. Lưu `clean_csv` và `clean_json` — dùng `df.to_csv()` và `write_json()`
5. `LocalEmbeddingIndex.build()` — đây là phần RAG cốt lõi: tạo collection `papers-baseline` và embedding manifest
6. `build_test_set()` — có guard `refresh_test_set` để không build lại khi đã có
7. `evaluate_pipeline()` — sinh `baseline_answers.json` và `baseline_metrics.json`
8. `run_data_quality_checks()` + `build_freshness_report()` — gọi module của TV3
9. `generate_phase1_report()` — tạo `phase1_report.md`
10. `build_agent()` + demo — wrapped trong try/except để không crash pipeline nếu LLM unavailable

### Input, output và contract

| Thành phần                   | Mô tả                                                                              |
| ------------------------------ | ----------------------------------------------------------------------------------- |
| Input                          | `Settings` (từ `load_settings()`), `list[PaperRecord]` từ TV1, clean `DataFrame` từ TV2, test set từ TV2, quality/freshness dict từ TV3 |
| Output                         | `baseline_metrics.json`, `baseline_answers.json`, `papers_embeddings.json` (manifest), `phase1_report.md`, `agent_demo_answers.json` |
| Module phụ thuộc             | `src/ingestion/crossref.py` (TV1), `src/ingestion/cleaning.py` (TV2), `src/evaluation/testset.py` (TV2), `src/observability/quality.py` và `reporting.py` (TV3) |
| Module sử dụng output        | `src/pipelines/corruption_flow.py` đọc `baseline_metrics.json` và `papers_embeddings.json` để so sánh; `data/reports/phase1_report.md` là artifact nộp cuối |
| Điều kiện lỗi cần xử lý | Guard `refresh_source` và `refresh_test_set` để không gọi lại API/rebuild không cần thiết; agent demo trong try/except để pipeline không crash nếu LLM quota hết; tạo thư mục cha trước khi ghi file |

### Cách xác minh

```bash
# Kiểm tra commit của phase1.py
git log --oneline src/pipelines/phase1.py
# Output thực tế: 77ec22e update_role_4  ← commit của mình (nhatngoonslaof)

# Kiểm tra baseline metrics đã được tạo
cat data/results/baseline_metrics.json
# Output thực tế:
# { "samples": 15, "retrieval_hit_rate": 1.0, "mean_token_f1": 0.418, ... }

# Kiểm tra embedding manifest
python3 -c "import json; d=json.load(open('data/embeddings/papers_embeddings.json')); print(d['collection_name'], len(d['documents']))"
# Output thực tế: papers-baseline 24
```

- **Kết quả mong đợi:** Baseline metrics tồn tại, collection `papers-baseline` có 24 documents.
- **Kết quả thực tế:** Khớp — `retrieval_hit_rate=1.0`, 24 documents trong collection.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/embeddings/papers_embeddings.json`, `data/reports/phase1_report.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Trong `phase1.py`, bước 2 (load records) cần quyết định: luôn gọi lại Crossref API hay đọc từ file đã lưu?
- **Các phương án đã cân nhắc:**
  - **Phương án A:** Luôn gọi API mỗi khi chạy `phase1.py` — đảm bảo data mới nhất nhưng tốn quota, và baseline thay đổi theo thời gian (không reproducible).
  - **Phương án B:** Dùng flag `settings.refresh_source`: chỉ gọi API khi `REFRESH_SOURCE=1` hoặc chưa có file raw; mặc định đọc từ snapshot đã lưu — baseline cố định, tái lập được.
- **Phương án đã chọn:** Phương án B.
- **Lý do:** Bài lab yêu cầu giữ nguyên baseline để so sánh với corrupted và repaired. Nếu mỗi lần chạy lại đều fetch data mới, comparison mất ý nghĩa vì baseline đã thay đổi. Flag `refresh_source` cho phép kiểm soát khi cần cập nhật có chủ đích.
- **Bằng chứng:** `data/raw/crossref_response.json` và `data/raw/crossref_records.json` giữ nguyên snapshot ban đầu xuyên suốt cả 3 phases (baseline, corrupted, repaired).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```
  ERROR: Package 'day10-data-observability-lab-student' requires a different Python: 3.14.3 not in '<3.14,>=3.11'
  ```
- **Lệnh hoặc bước tái hiện:**
  ```bash
  python3 -m venv .venv && source .venv/bin/activate && pip install -e .
  ```
- **Nguyên nhân gốc:** `pyproject.toml` khai báo `requires-python = ">=3.11,<3.14"` nhưng máy đang chạy Python 3.14.3 — phiên bản mới hơn upper bound đã đặt.
- **Cách xử lý:** Sửa `pyproject.toml` thành `requires-python = ">=3.11,<3.15"`. Đồng thời sửa `great-expectations>=1.16.1` → `>=0.16.1` vì phiên bản 1.16.1 không tồn tại (latest stable là 0.18.x).
- **Cách xác minh sau khi sửa:**
  ```bash
  pip install -e . && python -c "import chromadb, langchain; print('OK')"
  # Output: OK
  ```
- **Điều học được:** Upper bound trong `requires-python` nên được cập nhật khi Python minor version mới ra. Nên test cài đặt trên Python version mới nhất sớm, không đợi đến lúc chạy pipeline.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Dữ liệu từ Crossref đến vector index:** Crossref API trả về JSON → `parse_crossref_payload()` trích xuất thành `list[PaperRecord]` với `paper_id = DOI` → `build_clean_dataframe()` normalize, dedupe, tính `age_days`, tạo `text_for_embedding` → `LocalEmbeddingIndex.build()` dùng MiniLM encode `text_for_embedding` thành vectors và lưu vào ChromaDB collection `papers-baseline` kèm manifest JSON.

2. **Evaluation set và ground-truth doc IDs:** `build_test_set()` lấy các paper từ clean DataFrame, tạo câu hỏi (summary/authors/date/categories) và gắn `ground_truth_doc_ids = [paper_id]` từ đúng record. Khi evaluate, `retrieved_doc_ids` được so sánh với `ground_truth_doc_ids` để tính `retrieval_hit_rate`; text answer so với `ground_truth` để tính `token_f1`.

3. **Quality checks khác freshness monitoring:** Quality checks kiểm tra tính toàn vẹn cấu trúc **tại thời điểm hiện tại** (row count, uniqueness, null, blank, duplicate). Freshness monitoring nhìn vào chiều **thời gian** của dữ liệu — `published/age_days` so với ngưỡng 180 ngày — đo xem nội dung có còn mới không, không liên quan đến cấu trúc đúng sai.

4. **Phải dùng cùng test set cho cả 3 trạng thái:** Nếu test set thay đổi, metric thay đổi có thể đến từ câu hỏi khác, không phải từ corruption/repair. Giữ nguyên `test_set.json`, `top_k`, evaluator và ground truth đảm bảo mọi thay đổi metric là do **data**, không phải do cách đo.

5. **Repair thành công dựa trên:** Artifact — `papers_clean_repaired.csv` có 24 rows (bằng baseline, không phải 22 của corrupted); collection `papers-repaired` có 24 documents. Metric — `repaired_metrics.json` có `retrieval_hit_rate=1.00` và `mean_token_f1=0.418` bằng baseline. Quality check PASS trở lại trên repaired data.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân                                                                           |
| ---------------------- | -------: | --------: | -------: | ------------------------------------------------------------------------------------------------ |
| `retrieval_hit_rate`   |     1.00 |      0.80 |     1.00 | Giảm 20% khi corrupted (3 record bị drop → 3 câu hỏi không tìm được doc đúng trong index). Phục hồi hoàn toàn sau repair. |
| `mean_token_f1`        |     0.42 |      0.27 |     0.42 | Giảm 35% — noise và blank summary làm câu trả lời trích xuất sai nội dung. Repair phục hồi hoàn toàn. |
| `judge_accuracy`       |     0.33 |      0.20 |     0.33 | Thấp ngay cả baseline vì answer extraction literal, không phải generation. Corruption làm giảm thêm 0.13. |
| `mean_judge_score`     |     2.33 |      1.80 |     2.33 | Giảm 0.53 điểm khi corrupted. Cả baseline lẫn repaired đều ở mức trung bình. |
| Quality checks         | ✅ PASS  |  ❌ FAIL  | ✅ PASS  | Corrupted fail 3/8 checks: `paper_id_unique`, `summary_length`, `freshness`, `duplicate_rows`. |
| Freshness status       |  is_fresh=true | is_fresh=false (mean_age=537d, max=9999d) | is_fresh=true | `stale_date` đẩy age_days lên 9999, mean_age_days tăng từ 78 lên 537. |

### Kết luận từ số liệu

1. **[drop_record × 3]** → quality `row_count` giảm từ 24 xuống 22 → `retrieval_hit_rate` giảm từ 1.00 xuống 0.80 → `judge_accuracy` giảm từ 0.33 xuống 0.20. Đây là corruption ảnh hưởng **rõ nhất**: document bị xóa khỏi index → retrieval fail hoàn toàn → toàn bộ answer chain sai từ gốc.

2. **[Re-run cleaning từ raw snapshot]** → `papers_clean_repaired.csv` 24 rows → `papers-repaired` collection 24 docs → tất cả metric và quality signals phục hồi về mức baseline. Recovery hoàn toàn trong trường hợp này vì raw snapshot còn nguyên vẹn.

**Kết quả khác với kỳ vọng:** `judge_accuracy` baseline chỉ đạt 0.33, thấp hơn kỳ vọng. Nguyên nhân: `_extract_answer()` trong `qa.py` trả về literal text từ metadata (câu đầu của summary, hoặc `authors_joined`) thay vì câu trả lời tự nhiên. LLM judge đánh giá "materially correct" nhưng format literal thường không match đủ với ground truth. Hạn chế này tồn tại cả baseline và repaired, không phải do corruption.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data pipeline:** Orchestrator (`phase1.py`) không tự implement logic mà **gọi đúng module theo thứ tự dependency**. Thứ tự này quan trọng: clean data phải có trước khi build index, index phải có trước khi evaluate. Sai thứ tự một bước là toàn bộ pipeline crash.

2. **Data quality/observability:** Sau khi xem output thực tế, nhận ra quality checks (structural) và freshness (temporal) bắt được các vấn đề khác nhau. Corruption `stale_date` chỉ làm `freshness` fail nhưng không bị quality structural check bắt — cần cả hai mới đủ coverage.

3. **Ảnh hưởng của data đến RAG agent:** `drop_record` ảnh hưởng `retrieval_hit_rate` nhiều nhất (−20%) vì document bị xóa khỏi vector index, retrieval fail hoàn toàn. Đây là bằng chứng rõ ràng nhất rằng data quality quyết định chất lượng RAG, không phải prompt hay model.

### Nếu có thêm thời gian

Thêm corruption **field swap** — hoán đổi `authors_joined` giữa hai record khác nhau. Corruption này structural vẫn hợp lệ (không null, không blank) nên quality checks không phát hiện, nhưng câu trả lời "authors" sẽ sai hoàn toàn dù retrieval vẫn hit. Đây là loại lỗi nguy hiểm nhất vì khó phát hiện. Cách đo cải thiện: so sánh `judge_accuracy` cho riêng `question_type=authors` giữa baseline và corrupted.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lưu Quang Nhật
**Ngày xác nhận:** 2026-08-06
