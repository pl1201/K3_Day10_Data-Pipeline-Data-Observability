# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên          | Nguyễn Ngọc Sơn            |
| MSSV               | 2A202601948                |
| Khóa/Lớp           | K3                         |
| Tên nhóm           | C2-2                       |
| Vai trò chính      | Thành viên 1 - Source Ingestion |
| Repository         | https://github.com/pl1201/K3_Day10_Data-Pipeline-Data-Observability.git |
| Ngày hoàn thành    | 2026-08-06                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Kéo dữ liệu bài báo | `src/ingestion/crossref.py` | Từ khóa (Query) | File `data/raw/crossref_records.json` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Giải thích cấu trúc dữ liệu thô | Hỗ trợ TV2 (Cleaning) | TV2 hiểu các trường để tiến hành làm sạch |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Gọi API lấy dữ liệu | `src/ingestion/crossref.py` | File `crossref_records.json` | Mở thư mục `data/raw/` sẽ thấy file xuất hiện |
| Bàn giao file gốc làm "mỏ neo" | `data/raw/crossref_response.json` | File log chứa nguyên block JSON ban đầu | Dùng để dò lỗi ở bước Repair sau này |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:
Dữ liệu thô ban đầu (Raw records). Nhờ có dữ liệu này làm đầu vào thì pipeline mới có thể chạy. Lúc hệ thống bị báo lỗi data hỏng, module repair sẽ lấy lại file raw này của tôi để khôi phục lại từ đầu mà không cần phải gọi API tải lại.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Bài toán bắt đầu từ số 0, không có dữ liệu thì không thể triển khai Agent. Nhiệm vụ của tôi là gọi Crossref API để lấy metadata của các bài báo khoa học nhằm xây dựng corpus. Tuy nhiên, kết nối mạng không ổn định và cấu trúc JSON trả về phức tạp nên cần trích xuất và lọc các trường dữ liệu một cách chuẩn xác.

### Cách triển khai
Tôi triển khai hai hàm chính. Hàm `fetch_source_records` sử dụng thư viện `requests` để gọi API; hàm được bọc trong một vòng lặp có cơ chế xử lý ngoại lệ (try-except) với tối đa 3 lần thử lại (retries) và độ trễ (exponential backoff) để vượt qua các lỗi HTTP 429 và 503. Hàm thứ hai là `parse_crossref_payload`, thực hiện lấy payload JSON trả về, trích xuất và chuẩn hóa các trường thiết yếu như: Tiêu đề, Tác giả, Ngày xuất bản, Abstract... rồi serialize thành danh sách đối tượng `PaperRecord`.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Chữ khóa tìm kiếm (Query) và filter ngày tháng |
| Output                         | Danh sách bài báo dạng file `.json` |
| Module phụ thuộc               | Thư viện `requests` để gọi API |
| Module sử dụng output          | `src/ingestion/cleaning.py` của TV2 |
| Điều kiện lỗi cần xử lý        | Lỗi quá tải server (429) hoặc sập nguồn (503) |

### Cách xác minh

```bash
uv run python script/run_phase1.py
```

- **Kết quả mong đợi:** Màn hình in ra `[2/10] Fetching / loading raw records...`
- **Kết quả thực tế:** Code tải về thành công và báo đã lấy được 24 raw records.
- **Artifact/log:** `data/raw/crossref_records.json`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lúc tải bài báo về, nhóm cần 1 cái ID (mã định danh) không bao giờ thay đổi để sau này nếu có lỗi còn tìm ra đúng bài đó.
- **Các phương án đã cân nhắc:** 1 là tự đánh số thứ tự 1, 2, 3 ngẫu nhiên. 2 là dùng mã DOI (mã số gốc của bài báo trên mạng).
- **Phương án đã chọn:** Chọn mã DOI làm `paper_id`.
- **Lý do:** Mã DOI là chuẩn quốc tế của bài báo, không bao giờ bị trùng. Lỡ sau này nhóm làm hỏng data thì cứ dùng số DOI này map lại với file gốc để phục hồi cực kỳ chính xác.
- **Bằng chứng quyết định phù hợp:** Trong `crossref_records.json`, các `paper_id` đều là mã DOI chuẩn.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Bị lỗi `ModuleNotFoundError` khi gõ lệnh chạy python.
- **Lệnh hoặc bước tái hiện:** Gõ `python src/pipelines/phase1.py` trên Terminal.
- **Nguyên nhân gốc:** Lúc đó do tôi đứng chưa đúng thư mục gốc và chưa cấu hình biến môi trường `PYTHONPATH`, nên máy không hiểu code lấy thư viện ở đâu ra.
- **Cách xử lý:** Đổi sang dùng `uv run` hoặc kích hoạt `.venv` trước khi chạy.
- **Cách xác minh sau khi sửa:** Chạy lại script và không bị lỗi thiếu thư viện nữa.
- **Điều học được:** Môi trường code rất quan trọng, phải setup môi trường (venv) cẩn thận từ đầu để đảm bảo tính tái tạo.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu được lấy về dạng JSON thô từ Crossref API, sau đó chuyển cho module Cleaning để chuẩn hóa văn bản, xử lý null/duplicate. Data sạch tiếp tục được đưa qua module Retrieval để tạo embeddings (bằng sentence-transformers hoặc mô hình tương đương) và nạp vào vector database Chroma.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Evaluation set bao gồm các câu hỏi kiểm thử và `ground_truth_doc_ids` chứa ID gốc của tài liệu chứa câu trả lời. Hệ thống so sánh ID tài liệu mà RAG lấy ra được (retrieved) với ground truth để tính Hit Rate, và dùng LLM-as-a-judge so sánh câu trả lời của Agent với đáp án mẫu để tính Judge Score.
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   Quality checks tập trung vào tính toàn vẹn (không có null, không trùng lặp, độ dài summary hợp lệ). Freshness monitoring đánh giá tính cập nhật của dữ liệu bằng cách tính tuổi (`age_days`) từ ngày published, cảnh báo nếu dữ liệu quá cũ (stale).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để đảm bảo tính nhất quán (control variable). Nếu dùng test set khác, sự biến động về điểm số có thể do độ khó của câu hỏi chứ không phản ánh đúng tác động của việc phá hoại (corruption) hay sửa chữa dữ liệu.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Thành công khi Quality Checks trả về PASS, Freshness trả về YES, và các metrics của agent (`retrieval_hit_rate`, `mean_token_f1`, v.v.) khôi phục lại chính xác mức điểm đo được ở pha Baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |    100.0%|     80.0% |   100.0% | Corruption làm RAG không tìm thấy tài liệu gốc. Repair khôi phục hoàn toàn. |
| `mean_token_f1`      |     41.8%|     27.1% |    41.8% | Điểm F1 tụt mạnh khi dữ liệu hỏng. Phục hồi hoàn hảo. |
| `judge_accuracy`     |     33.3%|     20.0% |    33.3% | LLM judge đánh giá chất lượng câu trả lời giảm sút rõ rệt khi thiếu data. |
| `mean_judge_score`   |      2.33|      1.80 |     2.33 | Điểm trung bình giảm từ 2.33 xuống 1.8. |
| Quality checks         |      PASS|      FAIL |     PASS | Bắt được chính xác lỗi (duplicate, short summary) khi bị làm hỏng. |
| Freshness status       |       YES|        NO |      YES | Hệ thống phát hiện ngay bài báo bị sửa thành cũ (stale_rows). |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. **[Data corruption] → [quality/freshness signal thay đổi] → [agent metric thay đổi].**
   Việc xóa dữ liệu, làm trống summary và sửa đổi năm xuất bản đã làm hệ thống Observability báo FAIL (tăng duplicate, short summaries = 1, stale_rows = 1). Kéo theo Agent metric giảm mạnh (Hit Rate từ 100% xuống 80%).
2. **[Repair action] → [quality/freshness signal phục hồi] → [agent metric phục hồi hoặc chưa phục hồi].**
   Việc truy xuất ngược lại file `crossref_records.json` gốc để chạy lại Cleaning đã dọn sạch các lỗi giả lập, giúp Quality gate báo PASS và Hit Rate khôi phục hoàn toàn 100%.

Corruption nào ảnh hưởng rõ nhất và vì sao?
Việc "Blank summary" (làm trống tóm tắt) ảnh hưởng mạnh nhất đến Agent. Vì text embedding chủ yếu dựa vào nội dung tóm tắt; khi mất đoạn text này, semantic search không thể match câu hỏi của người dùng với bài báo, dẫn đến Hit Rate sụt giảm nghiêm trọng.

Kết quả nào khác với kỳ vọng ban đầu?
Điểm `mean_token_f1` của Baseline chỉ đạt 41.8%, thấp hơn so với suy nghĩ ban đầu của nhóm (thường RAG kỳ vọng khoảng 60%+). Nguyên nhân có thể do metadata trả về từ Crossref khá ngắn và học thuật, dẫn đến câu trả lời của Agent ngắn gọn, không match được nhiều token với câu trả lời lý tưởng của Evaluation set.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Sự quan trọng của Data Lineage: Luôn phải lưu file Raw ở chặng đầu tiên. Nó là Source of Truth rẻ và an toàn nhất để khôi phục dữ liệu khi pipeline gặp sự cố.
2. Observability không chỉ để xem: Các cổng kiểm tra (Quality Gates) giúp chặn dòng dữ liệu bẩn tràn vào Index. Nếu Index bị bẩn, chi phí để sửa đổi Vector Database sẽ rất cao.
3. Garbage In, Garbage Out: RAG Agent dù có dùng model xịn như GPT-4 hay Gemini 1.5 Pro thì vẫn sẽ trả lời sai lệch nếu dữ liệu nhúng (embeddings) bị thiếu hoặc nhiễu.

### Nếu có thêm thời gian

Nhóm có thể triển khai thêm cơ chế **Cảnh báo qua Email/Slack (Alerting)** khi Quality Check báo FAIL. Hiện tại báo cáo chỉ ghi ra file log tĩnh; nếu được tự động gửi cảnh báo, Data Engineer có thể can thiệp ngay lập tức thay vì phải tự mở file ra đọc.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Ngọc Sơn
**Ngày xác nhận:** 2026-08-06
