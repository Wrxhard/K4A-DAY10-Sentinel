# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                             |
| ------------------ | ------------------------------------------------------------------------------------- |
| Họ và tên       | Nguyễn Quốc Đạt                                                                |
| MSSV               | 2A202602369                                                                           |
| Khóa/Lớp         | K4-L3A                                                                                    |
| Tên nhóm         | Sentinel                                                                              |
| Vai trò chính    | Corruption & Integration Owner                                                       |
| Repository         | [github.com/Wrxhard/K4A-DAY10-Sentinel](https://github.com/Wrxhard/K4A-DAY10-Sentinel) |
| Ngày hoàn thành | 2026-09-25                                                                            |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data corruption scenarios      | `src/ingestion/corruption.py`, `corrupt_clean_dataframe()`           | Clean DataFrame từ `data/results/clean.json`          | Corrupted DataFrame, `data/results/corruption_log.json` | Hoàn thành |
| Corruption and repair integration      | `src/pipelines/corruption_flow.py`           | Raw/clean records, evaluation set, baseline artifacts          | Corrupted/repaired artifacts, metrics và `data/reports/corruption_report.md` | Hoàn thành |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                  | Thành viên/module được hỗ trợ | Kết quả                    |
| ----------------------------- | ------------------------------------ | ---------------------------- |
| Debug và tích hợp môi trường chạy CP5 | Pipeline evaluation và môi trường Python/PyTorch | Thiết lập `.venv311` tương thích; chạy được toàn bộ corruption flow và test suite |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh  |
| --------------------------- | ----------------------------- | ------------------------- | ---------------- |
| Triển khai đủ 6 kịch bản tiêm lỗi và ghi log | `src/ingestion/corruption.py`, `data/results/corruption_log.json` | 24 dòng corrupted, log ghi nhận đủ 6 scenario | Lệnh kiểm tra corruption độc lập và đọc `corruption_log.json` |
| Tích hợp đánh giá corrupted/repaired | `src/pipelines/corruption_flow.py`, `data/results/*_metrics.json` | Baseline, corrupted, repaired metrics và comparison report | `script/run_corruption_flow.py`; test suite 2 passed |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

`data/reports/corruption_report.md` xác nhận retrieval hit rate là 1.0 ở baseline, giảm còn 0.8 ở corrupted và phục hồi về 1.0 ở repaired.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần việc giải quyết việc kiểm chứng silent failure của RAG khi dữ liệu bị thiếu, nhiễu, cũ hoặc trùng lặp. Pipeline cần tạo được dữ liệu corrupted có kiểm soát, đo lại chất lượng và chứng minh khả năng phục hồi từ raw records.

### Cách triển khai

Hàm corruption làm việc trên bản sao của clean DataFrame, dùng seed cố định để kết quả tái lập. Sáu thao tác lần lượt loại bỏ 5 bản ghi mới nhất, xóa summary của 4 dòng, chèn noise vào embedding text của 4 dòng, rút ngắn 4 title, lùi ngày của 4 dòng về 5 năm trước và nhân đôi 5 dòng. Sau đó các trường dẫn xuất được xây dựng lại, số dòng đầu ra được giữ ở 24 và mọi thao tác được ghi log. Corruption flow chạy baseline, corrupted và repaired trên cùng evaluation set; repaired được dựng lại từ raw records.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Clean DataFrame, raw records, evaluation set và các đường dẫn trong settings |
| Output                         | Corrupted/repaired JSON, CSV, metrics, corruption log và comparison report |
| Module phụ thuộc             | `core.config`, `core.io`, `ingestion.clean`, `ingestion.loader`, `evaluation.metrics`, `quality`, `observability`, `vectorstore` |
| Module sử dụng output        | Evaluation pipeline, quality/freshness checks và báo cáo CP5 |
| Điều kiện lỗi cần xử lý | Thiếu clean artifact, thiếu raw records, DataFrame rỗng hoặc không tạo được artifact bắt buộc |

### Cách xác minh

```bash
.venv311\Scripts\python.exe script\run_corruption_flow.py
```

- **Kết quả mong đợi:** Tạo 24 corrupted rows, 24 repaired rows và report so sánh.
- **Kết quả thực tế:** `Corruption flow complete: 24 corrupted rows`; `Repair flow complete: 24 repaired rows`; test suite đạt `2 passed`.
- **Artifact/log:** `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần áp dụng đồng thời thao tác drop latest và duplicate rows nhưng vẫn giữ kích thước tập dữ liệu để so sánh metric công bằng.
- **Các phương án đã cân nhắc:** Chỉ xóa các dòng bị drop và chấp nhận kích thước thay đổi; hoặc drop bản ghi mới nhất rồi duplicate có kiểm soát để giữ 24 dòng.
- **Phương án đã chọn:** Drop 5 dòng mới nhất, sau đó duplicate 5 dòng còn lại để output vẫn có 24 dòng.
- **Lý do:** Giữ cùng kích thước đầu vào giúp so sánh baseline/corrupted/repaired dễ diễn giải hơn, đồng thời vẫn thể hiện được mất dữ liệu tươi và dữ liệu trùng lặp.
- **Bằng chứng quyết định phù hợp:** `corruption_log.json` ghi `input_rows: 24`, `output_rows: 24`; flow chạy hoàn tất và repaired metrics trở về đúng baseline.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `OSError: [WinError 126] Error loading "...torch\\lib\\shm.dll" or one of its dependencies.`
- **Lệnh hoặc bước tái hiện:** Chạy import `torch` hoặc `sentence_transformers` trong môi trường Python 3.13 trên Windows.
- **Nguyên nhân gốc:** PyTorch và dependency DLL trong môi trường Python 3.13 hiện tại không tương thích với hệ thống Windows đang dùng.
- **Cách xử lý:** Tạo `.venv311`, sử dụng Python 3.11 và bộ package CPU tương thích, sau đó chạy pipeline bằng interpreter của môi trường này.
- **Cách xác minh sau khi sửa:** Chạy `.venv311\Scripts\python.exe script\run_corruption_flow.py`; flow hoàn tất với 24 corrupted rows và 24 repaired rows.
- **Điều học được:** Khi lỗi xảy ra ở tầng native DLL, cần kiểm tra đồng thời phiên bản Python, PyTorch, kiến trúc CPU và dependency thay vì chỉ cài lại package ở môi trường cũ.

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** Không còn blocker chưa xử lý trong phần CP5.
- **Những gì đã loại trừ:** Đã kiểm tra lại interpreter, import dependency, test suite và artifact đầu ra.
- **Bước tiếp theo:** Không áp dụng; có thể bật thêm Ragas khi cần mở rộng đánh giá.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

Dữ liệu từ Crossref được load thành raw records, chuẩn hóa thành clean records, tạo `text_for_embedding` rồi đưa vào vector index. Evaluation set chứa câu hỏi và ground-truth document IDs để kiểm tra tài liệu đúng có được truy hồi hay không và dùng answer/reference để tính F1, judge accuracy và judge score. Quality checks kiểm tra tính hợp lệ của nội dung như title, summary, duplicate và trường bắt buộc; freshness monitoring tập trung vào độ mới của ngày xuất bản và số dòng stale. Cùng một test set giúp loại bỏ sai lệch do thay đổi câu hỏi giữa ba trạng thái. Repair thành công khi các artifact repaired hợp lệ, freshness được phục hồi và metrics repaired trùng hoặc trở về baseline; trong lần chạy này repaired retrieval hit rate, F1, judge accuracy và judge score đều khớp baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      1.0000 |       0.8000 |      1.0000 | Giảm 20 điểm phần trăm khi corrupted và phục hồi hoàn toàn. |
| `mean_token_f1`      |      0.7073 |       0.7588 |      0.7073 | Corrupted tăng trong bộ mẫu nhỏ, repaired trở về baseline. |
| `judge_accuracy`     |      0.6000 |       0.8000 |      0.6000 | Tăng ngoài kỳ vọng ở corrupted; repaired khớp baseline. |
| `mean_judge_score`   |      3.4000 |       3.8000 |      3.4000 | Cùng xu hướng với judge accuracy, cần bộ test lớn hơn để kết luận chắc chắn. |
| Quality checks         |      PASS |       FAIL |      PASS | Corruption bị phát hiện; dữ liệu sạch/repaired đạt kiểm tra. |
| Freshness status       |      True |       True |      True | Freshness tổng thể vẫn True dù có thao tác stale; cần theo dõi thêm theo dòng. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Các thao tác drop latest, blank, noise, truncate, stale date và duplicate làm quality checks chuyển sang FAIL; retrieval hit rate giảm từ 1.0 xuống 0.8.
2. Repair dựng lại dữ liệu từ raw records, đưa quality/freshness về trạng thái hợp lệ và đưa retrieval hit rate, F1, judge accuracy và judge score trở lại đúng baseline.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Mất các bản ghi mới nhất ảnh hưởng rõ nhất đến retrieval vì làm mất một phần tài liệu có thể là ground truth cho câu hỏi đánh giá; bằng chứng trực tiếp là retrieval hit rate giảm từ 1.0 xuống 0.8. Các lỗi summary, title, noise, stale date và duplicate đồng thời làm quality checks thất bại nhưng tác động lên các metric answer trong bộ 5 mẫu không đồng nhất.

Kết quả nào khác với kỳ vọng ban đầu?

Token F1, judge accuracy và mean judge score của corrupted cao hơn baseline, trái với kỳ vọng các metric đều giảm. Tôi kiểm tra lại bằng cách dùng cùng test set và đọc trực tiếp ba file metrics; kết quả này có thể do bộ đánh giá chỉ có 5 mẫu và corruption làm thay đổi context theo hướng thuận lợi cho một số câu hỏi. Vì vậy chỉ nên khẳng định chắc chắn sự suy giảm retrieval và sự phục hồi của repaired, không khẳng định mọi metric đều suy giảm.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Data pipeline cần bảo toàn raw records và tạo artifact trung gian để có thể tái tạo dữ liệu sạch.
2. Quality checks và freshness monitoring là tín hiệu quan sát quan trọng để phát hiện silent failure trước khi chỉ nhìn vào câu trả lời.
3. Chất lượng dữ liệu ảnh hưởng trực tiếp đến retrieval và có thể làm metric thay đổi không đồng nhất, nên cần đánh giá nhiều mẫu và nhiều tín hiệu.

### Nếu có thêm thời gian

Tăng evaluation set từ 5 mẫu lên một bộ lớn hơn, đồng thời gắn metric với từng corruption scenario. Khi đó có thể xác định chính xác lỗi nào làm giảm retrieval/answer quality và đặt ngưỡng cảnh báo đáng tin cậy hơn trong CI.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Quốc Đạt
**Ngày xác nhận:** 2026-09-25
