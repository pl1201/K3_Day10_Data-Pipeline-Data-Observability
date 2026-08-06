# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Phùng Văn Linh |
| MSSV | 2A202601992 |
| Khóa/Lớp | K3 |
| Tên nhóm | C2-2 |
| Vai trò chính | Thành viên 5 — Pipeline Integration & Evidence |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

Tôi phụ trách khối tích hợp và bằng chứng: kiểm tra các đầu ra từ ingestion, cleaning, evaluation, observability và corruption/repair có thể ghép thành một luồng tái lập được. Phạm vi gồm chạy và đối chiếu ba trạng thái **baseline → corrupted → repaired**, bảo đảm dùng cùng test set, cùng cấu hình đánh giá và các đường dẫn artifact riêng để không ghi đè baseline.

| Hạng mục | Module/artifact liên quan | Kết quả bàn giao |
| --- | --- | --- |
| Điều phối baseline | `src/pipelines/phase1.py`, `data/results/baseline_metrics.json` | Xác nhận luồng raw → clean → index → evaluate → quality/report tạo đủ artifact baseline |
| Điều phối corruption & repair | `src/pipelines/corruption_flow.py`, `data/results/corruption_log.json` | Đối chiếu corrupted/repaired dùng collection và file metrics riêng |
| Kiểm chứng so sánh | `data/reports/corruption_report.md` | Bảng delta metrics và quality/freshness cho ba trạng thái |
| Tái lập và tổng hợp bằng chứng | `script/run_phase1.py`, `script/run_corruption_flow.py` | Hướng dẫn chạy, checklist artifact và báo cáo nhóm |

## 3. Kết quả theo vai trò

| Kiểm tra | Bằng chứng | Kết quả |
| --- | --- | --- |
| Test set nhất quán | `data/eval/test_set.json` và ba file metrics | Cả baseline, corrupted và repaired đều đánh giá trên 15 mẫu |
| Baseline được khóa trước corruption | `baseline_metrics.json`, `papers_embeddings.json` | Retrieval hit rate 100.0%, mean token F1 41.8% |
| Corruption có ảnh hưởng đo được | `corrupted_metrics.json`, `corrupted_quality.json` | Hit rate giảm còn 80.0%; quality gate FAIL với 1 duplicate, 1 short summary, 1 stale row |
| Repair không sửa tay metrics | `repaired_metrics.json`, `repaired_quality.json` | Rebuild từ raw snapshot, phục hồi hit rate 100.0%, F1 41.8% và quality gate PASS |

## 4. Giải thích kỹ thuật

Điểm quan trọng của tích hợp là tách rõ ba trạng thái dữ liệu. `phase1.py` tạo baseline từ raw records, làm sạch, xây Chroma index, tạo test set, đánh giá và sinh quality/freshness report. `corruption_flow.py` sao chép baseline sạch để tạo dữ liệu corrupted, build index riêng và đánh giá bằng test set đã khóa. Sau đó flow đọc lại raw records tin cậy, chạy cleaning để tạo repaired data thay vì chỉnh trực tiếp dữ liệu hỏng, rồi build/evaluate lại.

Khi kiểm tra kết quả, tôi đối chiếu cùng bốn chỉ số: `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy` và `mean_judge_score`. Corruption làm giảm hit rate 20 điểm phần trăm (100% xuống 80%) và F1 14.7 điểm phần trăm (41.8% xuống 27.1%). Sau repair, các chỉ số trở về đúng mức baseline. Điều này cho thấy phép so sánh là nhất quán, đồng thời chứng minh raw snapshot và quality gate đủ để hỗ trợ khôi phục.

## 5. Cách tái lập

```bash
python -m pip install -e .
python script/run_phase1.py
python script/run_corruption_flow.py
```

Sau khi chạy, kiểm tra lần lượt `data/results/*_metrics.json`, `data/quality/*_quality.json`, `data/quality/*freshness.json` và `data/reports/corruption_report.md`. Không đưa API key hoặc nội dung `.env` vào báo cáo hay repository.

## 6. Phối hợp với nhóm

| Thành viên | Đầu vào nhận từ thành viên | Cách sử dụng trong tích hợp |
| --- | --- | --- |
| Nguyễn Ngọc Sơn | Raw Crossref records | Nguồn tin cậy để baseline và repair |
| Kim Mạnh Hùng | Clean schema, test set và corruption scenarios | Khóa contract dữ liệu và tiêu chí so sánh |
| Đinh Lê Quỳnh Phương | Quality/freshness checks, Markdown reports | Xác minh gate và diễn giải thay đổi tín hiệu |
| Lưu Quang Nhật | Baseline pipeline, cấu hình môi trường | Điều phối các bước baseline và artifact đầu ra |

## 7. Hạn chế và hướng phát triển

Điểm `judge_accuracy` baseline chỉ đạt 33.3%, nên pipeline đã chứng minh được tác động và khả năng recovery nhưng chưa phải là thước đo chất lượng trả lời cao. Hướng cải thiện là mở rộng test set, kiểm thử nhiều corruption seed, và bật Ragas khi thời gian chạy cho phép. Cũng nên đưa các đường dẫn lưu Chroma vào cấu hình tương đối để dễ tái lập trên máy khác.

## 8. Cam kết

- Báo cáo bám vào artifact và metrics có trong repository.
- Tôi hiểu luồng end-to-end và có thể giải thích cách giữ baseline, corrupted và repaired độc lập.
- Báo cáo không chứa secret hoặc API key.
