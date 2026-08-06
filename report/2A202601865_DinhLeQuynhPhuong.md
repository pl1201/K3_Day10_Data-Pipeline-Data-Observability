# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                        |
| ------------------ | ---------------------------------------------------------------- |
| Họ và tên       | Đinh Lê Quỳnh Phương                                            |
| MSSV               | 2A202601865                                                      |
| Khóa/Lớp         | K3                                                               |
| Vai trò chính    | P3 - Observability                                              |
| Ngày hoàn thành | 2026-08-06                                                       |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Quality & Freshness Checks | [quality.py](file:///d:/K3_Day10_Data-Pipeline-Data-Observability/src/observability/quality.py)<br>`run_data_quality_checks()`, `build_freshness_report()` | Cleaned `pd.DataFrame`, `Settings` | `baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`, `freshness_report.json`, `corrupted_freshness.json`, `repaired_freshness.json` | Hoàn thành |
| Reporting & Comparison | [reporting.py](file:///d:/K3_Day10_Data-Pipeline-Data-Observability/src/observability/reporting.py)<br>`generate_phase1_report()`, `generate_corruption_report()` | Metrics JSONs, Quality dicts, Source summary | `phase1_report.md`, `corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |
| Tích hợp Quality Gate vào pipeline | Thành viên 5 (`src/pipelines/phase1.py`, `corruption_flow.py`) | Chất lượng dữ liệu được kiểm tra tự động trước khi ghi đè index |
| Xác minh signal hỏng | Thành viên 4 (`src/ingestion/corruption.py`) | Xác nhận Quality Gate phát hiện đúng duplicate record, short summary và stale date |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng bộ quy tắc kiểm tra Data Quality | [quality.py:L17-L128](file:///d:/K3_Day10_Data-Pipeline-Data-Observability/src/observability/quality.py#L17-L128) | Xử lý 8 kiểm tra (row count, unique ID, non-null title, summary length, missing fields, duplicates, freshness) | Lệnh `uv run python script/run_phase1.py` sinh `data/quality/baseline_quality.json` |
| Theo dõi độ tươi dữ liệu (Freshness Monitoring) | [quality.py:L176-L238](file:///d:/K3_Day10_Data-Pipeline-Data-Observability/src/observability/quality.py#L176-L238) | Đo mốc ngày `published`, `age_days`, cảnh báo mốc > 180 ngày | Sinh file `freshness_report.json`, `corrupted_freshness.json` |
| Tự động hóa báo cáo Baseline & Comparison Markdown | [reporting.py:L14-L348](file:///d:/K3_Day10_Data-Pipeline-Data-Observability/src/observability/reporting.py#L14-L348) | Báo cáo Baseline 4 phần & Báo cáo So sánh 3 trạng thái (Baseline - Corrupted - Repaired) với delta | Sinh file `data/reports/phase1_report.md` và `corruption_report.md` |

### Output cụ thể tạo ra:
1. `data/quality/corrupted_quality.json`: Phát hiện chính xác `duplicate_count=1`, `short_summaries=1`, `stale_rows=1` làm trạng thái Quality Gate thất bại (`success=false`).
2. `data/reports/corruption_report.md`: Bảng so sánh 3 trạng thái chỉ ra suy giảm metrics từ Baseline (100% Hit Rate, 0.418 F1) xuống Corrupted (80% Hit Rate, 0.271 F1) và phục hồi hoàn toàn ở Repaired.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Trước khi thực hiện truy vấn RAG hoặc đưa dữ liệu vào Vector Store (ChromaDB), pipeline cần đảm bảo tính toàn vẹn của dữ liệu (Completeness, Uniqueness, Validity, Freshness). Nếu dữ liệu bị hỏng (corruption) mà không có hệ thống Observability phát hiện, Agent RAG sẽ đưa ra câu trả lời sai lệch mà không có cảnh báo.

### Cách triển khai
1. **Quality Gate (`run_data_quality_checks`)**: Duyệt DataFrame và trả về dictionary kết quả chi tiết từng chỉ số. Kiểm tra tiêu chí nghiêm ngặt:
   - `paper_id_unique`: duplicate ID = 0
   - `title_not_null`: non-null và non-blank
   - `summary_length`: độ dài tối thiểu >= 20 ký tự
   - `freshness`: `age_days` <= threshold (180 ngày)
2. **Freshness Monitoring (`build_freshness_report`)**: Xác định mốc dữ liệu cũ nhất/mới nhất, tính trung bình/trung vị số ngày phát hành (`age_days`) và gắn nhãn `is_fresh` dựa trên số lượng bản ghi quá hạn (`stale_rows`).
3. **Automated Reporting (`generate_phase1_report` & `generate_corruption_report`)**: Tổng hợp dữ liệu từ các file JSON metrics & quality thành định dạng Markdown chuẩn hóa với các biểu tượng trực quan (`✅ PASS`, `❌ FAIL`, delta `+`/`-`).

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ------ |
| Input | `df: pd.DataFrame` (dữ liệu đã cleaned/corrupted/repaired), `settings: Settings`, `metrics: dict` |
| Output | Dict kết quả quality & freshness; lưu file JSON trong `data/quality/` và file Markdown trong `data/reports/` |
| Module phụ thuộc | `src/core/config.py` (Settings & Data Paths), `src/core/utils.py` (`write_text`) |
| Module sử dụng output | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, báo cáo tổng hợp của nhóm |
| Điều kiện lỗi cần xử lý | DataFrame rỗng (`total_rows == 0`), thiếu cột `summary_chars` hoặc `age_days`, giá trị `published` chứa ngày lỗi/NaT |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Tự động tạo đầy đủ file `baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`, `phase1_report.md`, `corruption_report.md`.
- **Kết quả thực tế:** Tất cả các file đã được ghi thành công tại `data/quality/` và `data/reports/`.
- **Artifact/log:**
  - [baseline_quality.json](file:///d:/K3_Day10_Data-Pipeline-Data-Observability/data/quality/baseline_quality.json)
  - [corrupted_quality.json](file:///d:/K3_Day10_Data-Pipeline-Data-Observability/data/quality/corrupted_quality.json)
  - [repaired_quality.json](file:///d:/K3_Day10_Data-Pipeline-Data-Observability/data/quality/repaired_quality.json)

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn phương án trả về kết quả kiểm tra chất lượng dữ liệu để vừa phục vụ làm Quality Gate (chặn pipeline nếu FAIL) vừa phục vụ xuất báo cáo chi tiết.
- **Các phương án đã cân nhắc:**
  1. *Phương án A:* Ném ra exception (Raise Exception) ngay khi gặp lỗi chất lượng đầu tiên để dừng script ngay lập tức.
  2. *Phương án B:* Gom tất cả kết quả kiểm tra vào một object dictionary chuẩn hóa, bao gồm biến tổng thể `success: bool` và chi tiết `checks_detail`, ghi xuất ra file JSON trước khi ra quyết định dừng hay tiếp tục.
- **Phương án đã chọn:** Phương án B.
- **Lý do:** Giúp thu thập bức tranh toàn cảnh về các tín hiệu hỏng dữ liệu (ngay cả khi có nhiều lỗi xảy ra đồng thời như vừa lặp ID vừa dữ liệu quá hạn), tạo điều kiện cho script so sánh ở pha 5 (Corruption Flow) có thể đo lường và đưa vào báo cáo mà không bị sập script giữa chừng.
- **Bằng chứng quyết định phù hợp:** File `corrupted_quality.json` tổng hợp được đồng thời 3 lỗi: `duplicate_count: 1`, `short_summaries: 1`, `stale_rows: 1` với trạng thái `success: false`.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `KeyError: 'age_days'` hoặc `AttributeError` khi thực hiện `df["published"].max()` trên DataFrame bị corrupted chứa dữ liệu nổ ngày tháng hoặc thiếu cột `age_days`.
- **Lệnh hoặc bước tái hiện:** Chạy `run_data_quality_checks` trên DataFrame từ `src/ingestion/corruption.py` sau khi áp dụng noise/old date scenario.
- **Nguyên nhân gốc:** Khối corruption loại bỏ hoặc ghi đè một số cột chuẩn hóa làm mất cột tính sẵn `age_days` hoặc chuyển cột `published` về dạng không đúng chuẩn ISO datetime string.
- **Cách xử lý:** Thêm kiểm tra điều kiện an toàn (`if "age_days" in df.columns: ... else: ...`) và sử dụng `.dropna()` trước khi tính toán `mean()`, `median()`, `max()`. Fallback độ dài summary qua `df["summary"].astype(str).str.len()` khi cột `summary_chars` không tồn tại.
- **Cách xác minh sau khi sửa:** Lệnh `uv run python script/run_corruption_flow.py` chạy thành công mượt mà từ đầu đến cuối mà không bị dừng đột ngột.
- **Bài học kỹ thuật:** Các module observability phải có tính phòng thủ cao (defensive coding), không bao giờ được giả định rằng dữ liệu đầu vào luôn tuân thủ 100% schema chuẩn.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - Crossref REST API cung cấp danh sách bài báo JSON raw -> `crossref.py` parse và lưu thành raw snapshot -> `cleaning.py` lọc trùng, loại bỏ dữ liệu thiếu, tính toán `age_days` và chuẩn hóa chuỗi `text_for_embedding` -> Vectorizer biến đổi `text_for_embedding` thành vector embedding và nạp vào ChromaDB vector index.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - `test_set.json` chứa các cặp câu hỏi và `ground_truth_doc_ids`. Khi tìm kiếm vector (retrieval), hệ thống kiểm tra xem bài báo đúng (`ground_truth_doc_ids`) có nằm trong top-K bài báo được trả về không để tính `retrieval_hit_rate`. Đối với answer quality, câu trả lời sinh ra từ LLM được đối chiếu với câu trả lời mẫu (`ground_truth`) qua chỉ số Token F1 và điểm đánh giá của LLM Judge.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks**: Kiểm tra tính đúng đắn cấu trúc và thuộc tính dữ liệu tại mốc thời điểm hiện tại (ID không trùng, không blank title, summary đủ độ dài, không trùng lặp toàn dòng).
   - **Freshness monitoring**: Kiểm tra xu hướng thời gian của dữ liệu dựa trên mốc ngày xuất bản (`published` / `age_days`) so với thời gian chạy pipeline nhằm phát hiện dữ liệu lỗi thời (stale data > 180 ngày).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Nhằm đảm bảo tính nhất quán (apples-to-apples comparison). Khi giữ nguyên test set, sự thay đổi của các chỉ số (Hit Rate, Token F1, Judge Score) hoàn toàn phản ánh tác động của chất lượng dữ liệu lên hệ thống RAG chứ không bị nhiễu do độ khó khác nhau giữa các câu hỏi.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Dựa trên artifact: `repaired_quality.json` có `success: true`, `duplicate_count: 0`, `stale_rows: 0` và `repaired_freshness.json` có `is_fresh: true`.
   - Dựa trên metric: `repaired_metrics.json` ghi nhận `retrieval_hit_rate` phục hồi từ 80% lên 100%, `mean_token_f1` phục hồi từ 27.1% lên 41.8%, `judge_accuracy` phục hồi từ 20% lên 33.3%.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   100.0% |     80.0% |   100.0% | Corruption làm giảm 20% khả năng truy xuất đúng văn bản |
| `mean_token_f1`      |    41.8% |     27.1% |    41.8% | Chất lượng câu trả lời bị sụt giảm nghiêm trọng khi dữ liệu hỏng |
| `judge_accuracy`     |    33.3% |     20.0% |    33.3% | Tỷ lệ câu trả lời đạt điểm tối đa của Judge giảm rõ rệt |
| `mean_judge_score`   | 2.33/5.0 | 1.80/5.0 | 2.33/5.0 | Điểm đánh giá trung bình sụt giảm 0.53 điểm |
| Quality checks         |  ✅ PASS |   ❌ FAIL |  ✅ PASS | Phát hiện 1 duplicate ID và 1 short summary |
| Freshness status       |  ✅ Fresh|   ❌ Stale|  ✅ Fresh| Phát hiện 1 dòng chứa ngày phát hành năm 2000 (>180 ngày) |

### Kết luận từ số liệu

1. **[Data corruption] → [quality/freshness signal thay đổi] → [agent metric thay đổi]:**
   - Khi tiến hành chèn dữ liệu hỏng (xóa summary, lặp `paper_id`, chèn mốc ngày năm 2000), `corrupted_quality.json` phát hiện `duplicate_count=1`, `stale_rows=1` làm Quality Gate chuyển từ `PASS` sang `FAIL`. Đồng thời làm cho `retrieval_hit_rate` giảm từ 100% xuống 80% và `mean_token_f1` giảm từ 41.8% xuống 27.1%.

2. **[Repair action] → [quality/freshness signal phục hồi] → [agent metric phục hồi]:**
   - Sau khi thực hiện repair dữ liệu từ nguồn tin cậy (`data/raw/`), `repaired_quality.json` đạt `PASS` (`duplicate_count=0`, `stale_rows=0`), kéo theo `retrieval_hit_rate` phục hồi về 100% và `mean_token_f1` phục hồi về mức baseline 41.8%.

**Corruption ảnh hưởng rõ nhất:**
- Corruption xóa tóm tắt (`summary`) và lặp `paper_id` gây ảnh hưởng nặng nề nhất. Nó trực tiếp làm méo mó không gian embedding, dẫn đến việc retriever trả về các đoạn văn bản kém chất lượng, làm suy giảm lập tức `retrieval_hit_rate` và chất lượng câu trả lời của LLM.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Về Data Pipeline:** Pipeline dữ liệu không dừng lại ở việc ETL thành công mà phải có cơ chế quan sát (Observability) và kiểm soát chất lượng ở từng chặng.
2. **Về Data Quality & Observability:** Các tín hiệu quality check (completeness, uniqueness, freshness) là lá chắn đầu tiên giúp phát hiện bất thường trước khi dữ liệu xấu ảnh hưởng tới người dùng cuối.
3. **Về ảnh hưởng của Data đến RAG Agent:** Nguyên tắc "Garbage in, Garbage out" vô cùng rõ ràng trong RAG: dữ liệu nạp vào suy giảm chất lượng sẽ lập tức làm suy giảm cả độ chính xác truy vấn và khả năng sinh câu trả lời của LLM.

### Nếu có thêm thời gian
- Tích hợp công cụ observability chuyên nghiệp như **Great Expectations** hoặc **Evidently AI**, bổ sung cơ chế gửi cảnh báo tự động qua **Slack Webhook** hoặc **Email Alert** ngay khi Quality Gate bị rơi vào trạng thái `FAIL`.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đinh Lê Quỳnh Phương  
**Ngày xác nhận:** 2026-08-06

