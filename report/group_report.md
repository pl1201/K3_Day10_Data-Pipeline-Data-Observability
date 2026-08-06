# Báo cáo nhóm — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K3 |
| Tên nhóm | C2-2 |
| Repository | `K3_Day10_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò | Module/deliverable chính |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Ngọc Sơn | 2A202601948 | Source ingestion | `src/ingestion/crossref.py`, raw Crossref records |
| 2 | Kim Mạnh Hùng | 2A202601679 | Cleaning, test set & corruption scenarios | `cleaning.py`, `testset.py`, dữ liệu clean/test set |
| 3 | Đinh Lê Quỳnh Phương | 2A202601865 | Observability | `quality.py`, `reporting.py`, quality/freshness reports |
| 4 | Lưu Quang Nhật | 2A202601920 | Baseline pipeline & environment | `phase1.py`, cấu hình chạy baseline |
| 5 | Phùng Văn Linh | 2A202601992 | Pipeline integration & evidence | Đối chiếu baseline/corrupted/repaired, tái lập và báo cáo tổng hợp |

## 2. Tóm tắt kết quả

Nhóm xây dựng pipeline RAG từ metadata bài báo của Crossref: lấy raw snapshot, chuẩn hóa dữ liệu, tạo test set, lập Chroma index, đánh giá agent và theo dõi chất lượng dữ liệu. Baseline tạo được raw/clean artifacts, embedding manifest, 15 câu hỏi đánh giá, câu trả lời, metrics và báo cáo quality/freshness. Trên baseline, retrieval hit rate đạt 100.0% và mean token F1 đạt 41.8%.

Nhóm sau đó tạo corruption có kiểm soát (drop record, blank/noise summary, truncate title, stale date và duplicate) mà không sửa baseline. Trạng thái corrupted chỉ còn 22 hàng, quality gate FAIL do 1 duplicate, 1 summary ngắn và 1 stale row; retrieval hit rate giảm xuống 80.0% và F1 xuống 27.1%. Repair đọc lại raw snapshot rồi làm sạch, build index và đánh giá lại. Dữ liệu repaired có 24 hàng, quality/freshness PASS và metrics phục hồi về baseline. Kết quả cho thấy pipeline có thể phát hiện suy giảm qua observability và khôi phục bằng nguồn dữ liệu tin cậy. Giới hạn chính là `judge_accuracy` baseline còn 33.3% và Ragas chưa được bật trong lần chạy này.

## 3. Kiến trúc và luồng dữ liệu

```text
Crossref API → raw response/records → cleaning + data contract
→ Chroma embedding/index → shared test set → evaluation baseline
→ quality/freshness report → controlled corruption → re-index/evaluate
→ repair from raw snapshot → comparison report
```

| Khối | Input | Xử lý | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref API | Fetch, retry, parse, lưu snapshot | `data/raw/crossref_*.json` | Sơn |
| Cleaning/test set | Raw records | Normalize, dedupe, `age_days`, `text_for_embedding` | `data/clean/`, `data/eval/test_set.json` | Hùng |
| Index/evaluation | Clean data + test set | Chroma index, retrieval, answer evaluation | `data/embeddings/`, `data/results/*_metrics.json` | Nhật, Linh |
| Observability | Clean DataFrame + metrics | Quality/freshness checks, Markdown reporting | `data/quality/`, `data/reports/` | Phương |
| Corruption/repair | Baseline + raw snapshot | Corrupt có log; rebuild repaired data | `corruption_log.json`, corrupted/repaired artifacts | Hùng, Linh |
| Orchestration | Các artifact trên | Chạy, kiểm tra contract và so sánh | `phase1.py`, `corruption_flow.py` | Nhật, Linh |

## 4. Cách tái lập kết quả

```bash
python -m pip install -e .
python script/run_phase1.py
python script/run_corruption_flow.py
```

Không commit hoặc chèn API key/.env vào lệnh hay báo cáo. Các cấu hình chính: embedding model `sentence-transformers/all-MiniLM-L6-v2`, ChromaDB local, `top_k=3`, freshness threshold 180 ngày. Cùng `data/eval/test_set.json` được dùng cho cả ba trạng thái để so sánh công bằng.

| Lệnh | Kết quả cần kiểm tra |
| --- | --- |
| `python script/run_phase1.py` | `baseline_metrics.json`, `baseline_quality.json`, `freshness_report.json`, `phase1_report.md` |
| `python script/run_corruption_flow.py` | `corruption_log.json`, corrupted/repaired metrics & quality, `corruption_report.md` |

## 5. Data contract và chất lượng baseline

Cleaning tạo `paper_id` ổn định, title/summary, danh sách authors/categories đã join, `published`, `age_days` và `text_for_embedding`. Record thiếu ID/title hoặc trùng được xử lý trước khi index. Baseline có 24 hàng; các check `paper_id_unique`, title không rỗng, summary length và freshness đều PASS. Freshness report cho biết bài mới nhất là 2026-08-01, cũ nhất 2026-02-12, tuổi trung bình 78.2 ngày và không có stale row.

## 6. Thiết lập evaluation

| Thành phần | Cấu hình |
| --- | --- |
| Số câu hỏi | 15 |
| Loại câu hỏi | `summary`, `authors`, `date`, `categories` |
| Ground truth | Gắn với `ground_truth_doc_ids`/`paper_id` trong test set |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store | ChromaDB, collection riêng theo trạng thái |
| Metrics | retrieval hit rate, mean token F1, judge accuracy, mean judge score |

## 7. So sánh baseline, corrupted và repaired

| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| Samples | 15 | 15 | 15 |
| Retrieval hit rate | 100.0% | 80.0% | 100.0% |
| Mean token F1 | 41.8% | 27.1% | 41.8% |
| Judge accuracy | 33.3% | 20.0% | 33.3% |
| Mean judge score | 2.33/5 | 1.80/5 | 2.33/5 |
| Quality gate | PASS | FAIL | PASS |
| Freshness | Fresh | Not fresh | Fresh |

Corruption làm mất 2 hàng ròng (24 xuống 22), tạo 1 duplicate, 1 blank summary và 1 stale date. Các tín hiệu này khớp với `data/results/corruption_log.json` và được quality gate phát hiện. Repair xây lại dữ liệu từ raw snapshot, không copy hay chỉnh tay kết quả corrupted; sau repair, 24 hàng và toàn bộ signal quality trở lại bình thường.

## 8. Kết luận và hướng phát triển

Pipeline đã chứng minh được quan hệ giữa corruption, data-quality signal và chất lượng RAG. Việc giữ raw snapshot, test set và cấu hình đánh giá cố định giúp delta metrics có thể giải thích được. Các bước tiếp theo là mở rộng corpus/test set, chạy nhiều seed corruption, bật Ragas và dùng đường dẫn cấu hình tương đối để dễ tái lập trên nhiều máy.

## 9. Checklist nộp bài

- [x] Có raw, clean, test set, embeddings, answers, metrics, quality và reports.
- [x] Baseline/corrupted/repaired dùng artifact và collection riêng.
- [x] Cùng test set được dùng để so sánh ba trạng thái.
- [x] Corruption log đối chiếu được với quality signal và metrics.
- [x] Repair được xây lại từ raw snapshot.
- [x] Mỗi thành viên có báo cáo vai trò riêng, gồm `2A202601992_PhungVanLinh.md`.
