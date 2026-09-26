# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4-L3A              |
| Tên nhóm         | Sentinel     |
| Repository         | https://github.com/Wrxhard/K4A-DAY10-Sentinel |
| Ngày hoàn thành | 2026-09-25               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Trọng Phúc | 2A202602552 | Data Foundation & Quality (CP1, CP2) | `crossref.py`, `cleaning.py`, `quality.py`, `testset.py` |
| 2 | Nguyễn Văn Huy | 2A202602428 | RAG & Vector Index (CP2) | `index.py`, `agent.py`, `embeddings.py` |
| 3 | Nguyễn Triều Vương (Vuog23) | 2A202602422 | Observability & Baseline Pipeline (CP3) | `reporting.py`, `phase1.py` |
| 4 | Nguyễn Quốc Đạt | 2A202602369 | Corruption & Repair Integration (CP5) | `corruption.py`, `corruption_flow.py` |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành xuất sắc toàn bộ baseline pipeline (Phase 1) và data observability / corruption flow (CP5). Pipeline đã có khả năng:
- **Baseline pipeline**: Ingest data từ Crossref, clean và parse dữ liệu, chạy observability tests bằng Great Expectations, embed vào ChromaDB và benchmark tạo ra các metrics (`baseline_metrics.json`, `phase1_report.md`).
- **Corruption flow**: Mô phỏng 6 lỗi (như xoá dòng, nhân đôi, sửa ngày, làm nhiễu) khiến chất lượng giảm rõ rệt. Cụ thể, Data Quality Check fail và Hit Rate của mô hình RAG giảm từ 1.0 xuống 0.8.
- **Repair**: Xây dựng thành công cơ chế khôi phục từ original raw API. Nhờ đó, data quality trở lại PASS hoàn toàn, Hit rate khôi phục về lại 1.0. 
- Mọi giới hạn lớn về cài đặt thư viện (`great_expectations` bản 1.x) và fallback API đều đã được xử lý xong. Pipeline idempotent (chạy nhiều lần vẫn giữ nguyên state).

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records (Phúc)
    -> cleaning và data modeling (Phúc)
    -> embedding + ChromaDB index (Huy)
    -> evaluation baseline (Vương, Huy)
    -> quality/freshness reports (Phúc, Vương)
    -> corruption (Đạt)
    -> re-index và re-evaluate (Đạt)
    -> repair từ dữ liệu nguồn (Đạt)
    -> comparison report (Đạt, Vương)
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Query settings | Fetch API Crossref, fallback | `raw_api_response.json`, `crossref_records.json` | Phúc |
| Cleaning          | Raw Records    | Chuẩn hoá text, parse Date | `papers_clean.csv`, `papers_clean.json` | Phúc |
| Embedding/index   | Cleaned Data   | Vectorizing qua MiniLM     | ChromaDB sqlite3, `papers_embeddings.json` | Huy |
| Evaluation        | Test set       | Chấm QA theo Ground-truth  | `eval/test_set.json`, `baseline_answers.json` | Vương, Huy |
| Observability     | Cleaned Data   | Quality/Freshness checks   | `baseline_quality_report.json` | Phúc, Vương |
| Corruption/repair | Cleaned / Raw  | Tiêm lỗi và sửa lỗi        | `papers_clean_corrupted.json`, `papers_clean_repaired.json` | Đạt |
| Orchestration     | Code config    | Định tuyến pipeline logic  | `phase1.py`, `corruption_flow.py` | Đạt, Vương |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | openai         |
| `LLM_MODEL`                | gpt-4o-mini         |
| Embedding model              | sentence-transformers/all-MiniLM-L6-v2         |
| Số lượng Crossref records | 24 (max_results trong config)         |
| Retrieval `top_k`           | 4         |
| Freshness threshold          | 180 ngày         |
| Random seed, nếu có        | Không cố định         |

### Lệnh cài đặt

```bash
uv sync
```

### Lệnh chạy

Baseline:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | Mới nhất theo Git | `data/results/baseline_metrics.json` |
| Corruption flow   | Thành công | Mới nhất theo Git | `data/results/repaired_metrics.json` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref API endpoint |
| Query/filter                | Default query theo repo template  |
| Thời điểm lấy dữ liệu | Lúc chạy pipeline                           |
| Số record nhận được    | ~100 records                        |
| Cơ chế retry/backoff      | Timeout 10s, fallback đọc bản offline nếu rớt mạng |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | string | Có | Mã DOI của bài báo | Validate Quality fail nếu trùng/thiếu |
| `title` | string | Có | Tựa bài báo | Lọc rỗng và fallback |
| `summary` | string | Có | Nội dung abstract | Kiểm tra chiều dài tối thiểu 30 |
| `text_for_embedding` | string | Có | String combine dùng để embed | Nếu thiếu, pipeline fail |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Kiểm tra title/summary không null | Completeness  | Hầu hết | `baseline_quality_report.json` (success) |
| Kiểm tra dòng rỗng | Validity | Vài dòng (nếu có) | Logs và reports (Great Expectations) |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:
- `text_for_embedding`: Nối title, summary và keyword/categories thành một chuỗi văn bản.
- `document ID`: Lấy trực tiếp DOI từ Crossref response.
- `age_days`: Tính độ lệch ngày xuất bản so với hiện tại để làm base cho Freshness.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 10 câu (từ test_set)                 |
| Các `question_type`                    | `summary`, `authors`, `date`, `categories`                  |
| Ground-truth document ID                 | Từ `paper_id` trong clean dataframe     |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2`                  |
| Vector store/collection                  | ChromaDB (`papers-baseline`)                 |
| Retrieval `top_k`                       | 4                   |
| LLM provider/model                       | openai / gpt-4o-mini                   |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:
Sử dụng chung 1 bộ Test-Set (Ground truth, query question cố định) để đo lường công bằng sự thay đổi của Hit rate/F1 khi source Data bên dưới thay đổi.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | Chứa response từ API |
| Cleaned dataset          | `data/clean/`                        | Có | Cleaned CSV/JSON |
| Embedding manifest/index | `data/embeddings/`                   | Có | Vector logs |
| Evaluation set           | `data/eval/`                         | Có | Test-set |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Đầy đủ |
| Quality/freshness        | `data/quality/`                      | Có | `baseline_quality_report.json` |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Report |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.0 | Rất hoàn hảo, mọi câu trả lời đều trỏ đúng document ground-truth  |
| `mean_token_f1`      |     0.7073 | Khá ổn để agent trả lời sát ngữ nghĩa                           |
| `judge_accuracy`     |     0.6000 | Tỉ lệ chấp nhận của LLM judge.                           |
| `mean_judge_score`   |     3.4000 | Thang điểm trung bình của câu trả lời                           |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| Null check | Completeness | Title/ID not null | Pass | `baseline_quality_report.json` |
| Unique ID | Uniqueness | Không có DOI trùng lặp | Pass | `baseline_quality_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | `data/clean/papers_clean.csv`            |
| Trạng thái baseline      | Fresh               |
| Lý do                     | Tỉ lệ dòng stale ít hơn ngưỡng 25%. |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop latest | Xóa 5 record mới nhất | 5 | Freshness giảm | Hit Rate rớt xuống 0.8 | Nạp lại pipeline từ raw records. |
| Duplicate rows | Gấp đôi 5 dòng ngẫu nhiên | 5 | Quality Uniqueness FAIL | Duplicate làm rối RAG | Nạp lại pipeline từ raw |

Corruption log:
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có đầy đủ
- Nhận xét: Ghi đủ 6 loại lỗi.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:
Idempotent Repair Pipeline được thiêt kế để lấy lại thẳng dữ liệu từ `data/raw/crossref_records.json` (Source of Truth không thể thay đổi) và chạy lại các process (cleaning, vectorizing, indexing). Đảm bảo pipeline idempotent và sạch.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      1.0 |       0.8 |      1.0 | Giảm 0.2 | Phục hồi 100% | RAG search rất nhạy với mất data. |
| `mean_token_f1`        |      0.7073 |       0.7588 |      0.7073 | Tăng vô lý | Phục hồi | Lỗi metric do test set ít. |
| `judge_accuracy`       |      0.60 |       0.80 |      0.60 | Tăng vô lý | Phục hồi | Tương tự F1. |
| `mean_judge_score`     |      3.40 |       3.80 |      3.40 | Tăng vô lý | Phục hồi | Tương tự F1. |
| Quality checks pass/fail |      PASS |       FAIL |      PASS | Gây fail GX | Phục hồi | Observability hoạt động cực tốt. |
| Freshness status         |      True |       True |      True | Không suy suyển | - | Cần test set bự hơn. |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:
1. Xóa các bài báo mới nhất và thêm duplicate data → Great Expectations báo cáo FAIL (Quality checks fail) → VectorDB bị hụt data → Agent truy xuất context sai → `retrieval_hit_rate` sụt giảm.
2. Chạy cơ chế khôi phục lấy lại data từ Raw → Clean Pipeline thành công → Quality Check trở lại PASS → Mô hình lấy đúng dữ liệu sạch → Hit Rate phục hồi (từ 0.8 lên 1.0).

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:
- **Triệu chứng:** Pipeline báo `OSError: [WinError 126] Error loading "...torch\\lib\\shm.dll"` khi Đạt tích hợp vào CP5 và chạy pipeline ở local. Hoặc lỗi phiên bản thư viện với Great Expectations.
- **Nguyên nhân:** PyTorch conflict Windows / Python 3.13 hoặc API Great Expectations bị lỗi thời trong môi trường local.
- **Cách xử lý:** Nhóm set up môi trường chuẩn, giới hạn version Python (dùng 3.11), và refactor code Quality.py sang dùng Great Expectations API 1.x (Context, DataSource). 
- **Cách xác minh:** Pipeline chạy trơn tru qua `run_corruption_flow.py` (2 passed pytest).

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Sample evaluation quá nhỏ (5-10 câu hỏi) | Làm cho F1 và Accuracy của tập bị lỗi nhảy điểm ngẫu nhiên, không thống kê chính xác | Tạo một evaluation pipeline gen hàng loạt 100 câu hỏi |
| Local vector DB, không scale được | Ảnh hưởng tốc độ chạy nếu nạp 1 triệu bài báo | Triển khai vector DB trên Cloud |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
