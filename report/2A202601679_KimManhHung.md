# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Kim Mạnh Hùng |
| MSSV | 2A202601679 |
| Khóa/Lớp | K3 |
| Vai trò chính | P2 — Cleaning & Test set |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

Tôi phụ trách vai trò **P2: Cleaning & Test set**. Nhiệm vụ chính của tôi là thiết kế quy tắc làm sạch dữ liệu thô (raw data) nhận được từ Crossref API, chuẩn hóa các trường thông tin để phục vụ cho việc nhúng vector (embedding) và thiết kế thuật toán tự động xây dựng bộ câu hỏi kiểm chứng (evaluation test set).

| Module/deliverable | File hoặc thành phần phụ trách | Input | Output bàn giao |
| --- | --- | --- | --- |
| Data Cleaning | [cleaning.py](file:///d:/Day10_2A202601679_KimManhHung/K3_Day10_Data-Pipeline-Data-Observability/src/ingestion/cleaning.py) | List `PaperRecord` thô từ Crossref ingestion | Dataframe đã chuẩn hóa các trường, tính `age_days`, loại trùng lặp và tạo cột embedding |
| Test set Generation | [testset.py](file:///d:/Day10_2A202601679_KimManhHung/K3_Day10_Data-Pipeline-Data-Observability/src/evaluation/testset.py) | Dataframe sạch đã được chuẩn hóa | Bộ câu hỏi kiểm chứng (`test_set.json`) chứa các dạng câu hỏi khác nhau về tác giả, ngày đăng, tóm tắt |

## 3. Kết quả đã bàn giao

| Nhiệm vụ | Kết quả cụ thể | Cách xác minh |
| --- | --- | --- |
| Làm sạch dữ liệu | Xây dựng thành công DataFrame sạch từ Crossref records, lọc bỏ records lỗi hoặc thiếu tiêu đề. | [baseline_quality.json](file:///d:/Day10_2A202601679_KimManhHung/K3_Day10_Data-Pipeline-Data-Observability/data/quality/baseline_quality.json) báo `total_rows=24` ở baseline, các trường được chuẩn hóa đúng schema. |
| Xây dựng test set | Tạo bộ câu hỏi kiểm thử bao gồm các dạng khác nhau từ các bài báo tiêu biểu. | [test_set.json](file:///d:/Day10_2A202601679_KimManhHung/K3_Day10_Data-Pipeline-Data-Observability/data/eval/test_set.json) chứa 15 câu hỏi đa dạng loại (`summary`, `authors`, `date`, `categories`). |
| Ràng buộc Schema | Đảm bảo tính toàn vẹn của dữ liệu clean để các bước sau không bị lỗi index. | Quality gates cho `paper_id_unique` và `title_not_null` ở baseline đều PASS. |

## 4. Giải thích phần kỹ thuật

### Vấn đề cần giải quyết

Dữ liệu thô từ API Crossref thường không đồng nhất: tác giả và phân loại dạng list/chuỗi phức tạp, ngày đăng định dạng không nhất quán hoặc thiếu sót. Hơn thế nữa, để đánh giá RAG một cách khách quan, ta cần một bộ câu hỏi đánh giá có câu trả lời chuẩn (ground truth) gắn chặt với ID tài liệu nguồn, tránh việc LLM tự sinh câu trả lời không có trong tài liệu.

### Cách triển khai

1. Trong [cleaning.py](file:///d:/Day10_2A202601679_KimManhHung/K3_Day10_Data-Pipeline-Data-Observability/src/ingestion/cleaning.py):
   - Đọc từng `PaperRecord`, loại bỏ các bản ghi không có `paper_id` hoặc tiêu đề trống.
   - Sử dụng `.strip()` để làm sạch khoảng trắng thừa, chuẩn hóa danh sách tác giả (`authors_joined`) và phân loại (`categories_joined`) bằng cách join các phần tử với dấu phẩy.
   - Thử parse ngày tháng xuất bản (`published`) và cập nhật (`updated`) theo format `%Y-%m-%d`, tính tuổi thọ bài báo (`age_days`) so với `run_date` để hỗ trợ đo lường độ mới (freshness).
   - Ghép nối thông tin thành trường `text_for_embedding` phục vụ trực tiếp cho ChromaDB Index.
   - Loại bỏ các bản ghi trùng lặp thông qua `drop_duplicates(subset=["paper_id"])`.
2. Trong [testset.py](file:///d:/Day10_2A202601679_KimManhHung/K3_Day10_Data-Pipeline-Data-Observability/src/evaluation/testset.py):
   - Chọn ra 5 bài báo đại diện từ các phân vùng khác nhau của corpus (đầu, giữa, cuối) để làm mẫu sinh câu hỏi.
   - Tự động sinh 4 loại câu hỏi chính cho mỗi bài báo: Hỏi về tóm tắt (`summary`), tác giả (`authors`), ngày xuất bản (`date`), và chủ đề (`categories`).
   - Cung cấp ground truth và mapping với `ground_truth_doc_ids` tương ứng của bài báo đó.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | List các đối tượng `PaperRecord` thô từ module Ingestion. |
| Output | Dataframe sạch dạng bảng và tệp tin câu hỏi `test_set.json` chứa thông tin kiểm thử. |
| Module phụ thuộc | Ingestion (`src/ingestion/crossref.py`) |
| Module dùng output | Indexing (`src/retrieval/index.py`), Evaluation (`src/evaluation/metrics.py`) và Observability |
| Lỗi được xử lý | Loại bỏ lỗi parse ngày tháng do sai định dạng bằng cách bắt ngoại lệ `ValueError`, xử lý triệt để records trùng lặp. |

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi xây dựng dữ liệu đầu vào cho mô hình nhúng (Embedding), cần quyết định cách cấu trúc dữ liệu văn bản từ bài báo thô để vector database lưu trữ tối ưu nhất.
- **Phương án 1:** Chỉ nhúng nội dung tóm tắt (`summary`) của bài báo. Phương án này tiết kiệm dung lượng lưu trữ nhưng làm mất thông tin tiêu đề và tác giả, khiến RAG không thể trả lời các câu hỏi metadata.
- **Phương án 2:** Thiết kế trường dữ liệu đặc biệt `text_for_embedding` bằng cách kết hợp có cấu trúc: `Title: {title}\nAuthors: {authors_joined}\nSummary: {summary}`.
- **Phương án chọn:** Phương án 2.
- **Lý do:** Giúp mô hình embedding học được cả ngữ cảnh từ tiêu đề, tác giả lẫn nội dung tóm tắt, giúp retrieval hit rate tăng lên tối đa khi người dùng hỏi các câu hỏi liên quan đến metadata.
- **Bằng chứng:** Kết quả `retrieval_hit_rate` của baseline đạt tối đa 100% đối với cả 4 loại câu hỏi metadata lẫn nội dung.

## 6. Một lỗi/blocker đã xử lý

- **Triệu chứng:** Khi chạy build test set đối với dữ liệu thử nghiệm rất ít (dưới 5 bài báo), hàm `iloc` bị lỗi chỉ mục ngoài phạm vi (out of bounds indexer).
- **Nguyên nhân gốc:** Thuật toán phân vùng index `[0, len(df)//4, len(df)//2, (3*len(df))//4, len(df)-1]` giả định chiều dài dataframe luôn >= 5. Khi corpus nhỏ hơn 5, chỉ số tính toán sẽ vượt quá độ dài danh sách.
- **Cách xử lý:** Bổ sung điều kiện kiểm tra `if len(df) < 5:` để lấy toàn bộ dataframe làm mẫu sinh câu hỏi thay vì lấy phân vùng.
- **Kết quả:** Code chạy an toàn ngay cả với corpus nhỏ, tránh crash hệ thống khi dữ liệu thô bị drop nhiều.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index:** Crossref API trả về raw JSON payload, được parse thành list `PaperRecord` và lưu dưới dạng raw snapshot. Quá trình cleaning chuẩn hóa các trường (title, summary, authors, categories, published date), tính toán `age_days` và ghép các trường thành `text_for_embedding`. Dữ liệu clean được đưa vào ChromaDB để tạo vector index bằng cách sử dụng MiniLM embeddings.
2. **Đo lường chất lượng:** Evaluation set tạo ra các câu hỏi từ các tài liệu đã clean. Ground-truth document IDs được gán kèm để đối chiếu xem hệ thống retrieval có lấy ra đúng tài liệu chứa câu trả lời hay không, từ đó tính toán `retrieval_hit_rate` và chất lượng câu trả lời bằng LLM (`judge_accuracy`, `mean_token_f1`).
3. **Quality checks vs Freshness monitoring:** Quality checks kiểm tra tính toàn vẹn và hợp lệ cấu trúc của dữ liệu (nulls, duplicates, summary length). Freshness monitoring đo lường độ mới của dữ liệu dựa trên thời gian xuất bản (`age_days` vs threshold 180 ngày).
4. **Tại sao giữ nguyên test set:** Để đảm bảo tính so sánh khách quan và nhất quán (apples-to-apples comparison) giữa baseline, corrupted và repaired.
5. **Đánh giá Repair thành công:** Dựa trên việc quality checks trả về `PASS` (không còn lỗi duplicates, short summaries, stale rows) và các chỉ số RAG (`retrieval_hit_rate` phục hồi về 100%, `mean_token_f1` quay lại 41.8%).

## 8. Phân tích kết quả

### Bảng số liệu đối chiếu

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | :---: | :---: | :---: | --- |
| `retrieval_hit_rate` | 100.0% | 80.0% | 100.0% | Giảm 20% do drop record và noise summary, phục hồi hoàn toàn sau repair. |
| `mean_token_f1` | 41.8% | 27.1% | 41.8% | Giảm mạnh do summary trống/noise, hồi phục sau khi build lại từ raw. |
| `judge_accuracy` | 33.3% | 20.0% | 33.3% | Độ chính xác của câu trả lời giảm sút khi thiếu context chuẩn. |
| `mean_judge_score` | 2.33/5.00 | 1.80/5.00 | 2.33/5.00 | Điểm đánh giá trung bình từ LLM phản ánh rõ chất lượng context. |
| Quality checks | ✅ PASS | ❌ FAIL | ✅ PASS | Phát hiện 1 duplicate, 1 short summary, 1 stale row ở pha corrupted. |
| Freshness status | ✅ PASS | ❌ FAIL | ✅ PASS | Phát hiện stale row với `age_days` cực lớn (9999 ngày) do stale_date. |

### Kết luận từ số liệu

1. **[Data corruption] -> [quality/freshness signal thay đổi] -> [agent metric thay đổi]:** Việc áp dụng `stale_date` (2000-01-01) làm freshness status chuyển sang `FAIL` (stale_rows=1), đồng thời `blank_summary` và `noise_summary` làm quality gate báo `FAIL` (short_summaries=1), kéo theo `retrieval_hit_rate` giảm 20.0% và `mean_token_f1` giảm 14.7%.
2. **[Repair action] -> [quality/freshness signal phục hồi] -> [agent metric phục hồi]:** Tiến hành reload dữ liệu nguồn đáng tin cậy từ raw snapshot và chạy lại cleaning giúp loại bỏ hoàn toàn duplicate, phục hồi summary gốc và sửa lại date. Kết quả quality/freshness gate quay lại `PASS` và toàn bộ metrics RAG phục hồi về mức baseline.

## 9. Cách chạy và xác minh

```powershell
# Kích hoạt môi trường và chạy baseline
uv run python script/run_phase1.py

# Chạy corruption và recovery flow
uv run python script/run_corruption_flow.py
```

## 10. Cam kết

- [x] Báo cáo phản ánh đúng phần việc P2 — Cleaning & Test set.
- [x] Có thể giải thích luồng end-to-end và contract giữa các module.
- [x] Không ghi nhận kết quả chưa được kiểm chứng.
- [x] Không chứa API key, token hoặc secret.
- [x] Nội dung được viết riêng cho vai trò P2.

**Họ và tên:** Kim Mạnh Hùng
**Ngày xác nhận:** 2026-08-06
