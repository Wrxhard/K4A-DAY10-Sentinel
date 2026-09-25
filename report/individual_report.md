# Báo cáo vai trò cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Triều Vương |
| MSSV | 2A202602422 |
| Khóa/Lớp | K4 |
| Tên nhóm | Sentinel |
| Vai trò chính | Observability & Evaluation Lead |
| Repository | [Wrxhard/K4A-DAY10-Sentinel](https://github.com/Wrxhard/K4A-DAY10-Sentinel) |
| Ngày báo cáo | 2026-09-25 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu và tích hợp

| Phần việc | File/hàm liên quan | Input | Output | Trạng thái |
| --- | --- | --- | --- | --- |
| Tích hợp baseline pipeline end-to-end | `src/pipelines/phase1.py::main` | Raw records từ `data/raw/crossref_records.json`; cấu hình trong `src/core/config.py` | Clean CSV/JSON, baseline Chroma collection, evaluation results, quality/freshness reports | Hoàn thành và đã chạy |
| Tạo báo cáo baseline | `src/observability/reporting.py::generate_phase1_report` | Source summary, metrics, quality và freshness results | `data/reports/phase1_report.md` | Hoàn thành và đã sinh artifact |
| Tích hợp evaluation và quality gate | `src/evaluation/metrics.py`, `src/evaluation/testset.py`, `src/observability/quality.py` | Clean dataframe, test set cố định, Chroma index | Hit rate, token F1, judge metrics và GX validation result | Baseline hoàn thành; corruption/repair chưa chạy |

Trong phạm vi CP3, phần việc trực tiếp được ghi nhận ở commit `bc65bf6` là nối các module thành baseline pipeline, sinh báo cáo và xác minh kết quả. Các module evaluation set và Great Expectations được tích hợp theo contract hiện có; báo cáo này không nhận quyền sở hữu việc viết lại toàn bộ các module đó.

### Việc hỗ trợ ngoài phạm vi chính

Không có hoạt động hỗ trợ ngoài phạm vi được ghi nhận trong commit và artifacts dùng cho báo cáo này.

## 3. Kết quả theo vai trò

| Nhiệm vụ | File/hàm/artifact | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Kết nối load raw, cleaning, quality gate, indexing và evaluation | `src/pipelines/phase1.py::main` | 24 hồ sơ sạch; baseline collection có 24 vectors; quality checks thành công | Chạy `script/run_phase1.py`; kiểm tra `baseline_quality_report.json` và collection `papers-baseline` |
| Ghi baseline report từ kết quả chạy | `src/observability/reporting.py::generate_phase1_report` | `data/reports/phase1_report.md` có source summary, metrics, quality và freshness | Mở report và đối chiếu JSON artifacts |
| Khắc phục việc tải model khi môi trường không có mạng | `src/retrieval/embeddings.py::_load_model` | Dùng snapshot MiniLM đã cache trong `.model-cache` khi có sẵn | Chạy lại baseline trong môi trường offline, exit code 0 |

Kết quả cụ thể: baseline có `retrieval_hit_rate = 1.0` trên 5 câu hỏi; GX quality status là `PASS`; freshness report ghi nhận 0/24 hồ sơ quá ngưỡng 180 ngày.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Các module ingestion, cleaning, indexing, evaluation và observability cần được gọi theo đúng thứ tự để tạo baseline có thể kiểm tra lại. Pipeline cũng phải dừng trước khi index/evaluate nếu dữ liệu rỗng hoặc quality gate thất bại, và cần có một báo cáo tổng hợp thay vì chỉ để kết quả rời rạc trong JSON.

### Cách triển khai

`main()` nạp cấu hình và dùng raw snapshot sẵn có khi không bật `REFRESH_SOURCE`. Sau đó pipeline làm sạch records, ghi CSV/JSON, chạy Great Expectations và lưu kết quả validation. Nếu validation thất bại, pipeline dừng trước bước index. Khi dữ liệu hợp lệ, pipeline tính freshness, tạo collection `papers-baseline`, nạp hoặc tạo benchmark, chạy evaluation rồi sinh Markdown report.

Model MiniLM được lưu trong cache cục bộ của project. Khi snapshot cho model đã có, `_load_model()` mở snapshot trực tiếp để tránh yêu cầu kiểm tra metadata trên Hugging Face Hub mỗi lần chạy.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `data/raw/crossref_records.json`; mỗi record có `paper_id`, `title`, `summary`, authors, categories và ngày xuất bản |
| Output | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`, `data/embeddings/papers_embeddings.json`, `data/eval/test_set.json`, baseline results, quality/freshness JSON và `data/reports/phase1_report.md` |
| Module phụ thuộc | `core.config`, `core.utils`, ingestion, `evaluation.testset`, `evaluation.metrics`, `observability.quality`, `observability.reporting`, `retrieval.index` |
| Module sử dụng output | Baseline report và các artifacts được dùng để kiểm tra CP3; corruption flow dự kiến dùng clean data, baseline metrics và cùng evaluation set |
| Điều kiện lỗi cần xử lý | Raw input rỗng, cleaning không tạo được records, quality gate fail, hoặc embedding model chưa có trong cache khi môi trường không truy cập được Hub |

### Cách xác minh

```powershell
$env:LLM_PROVIDER = "mock"
$env:HF_HUB_OFFLINE = "1"
.\.venv\Scripts\python.exe script/run_phase1.py
```

- **Kết quả mong đợi:** Pipeline kết thúc với exit code 0 và tạo baseline artifacts.
- **Kết quả thực tế:** Exit code 0; 24 clean papers; retrieval hit rate `1.000`; quality checks `PASS`.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/quality/baseline_quality_report.json`, `data/quality/freshness_report.json`, `data/reports/phase1_report.md`.

Lệnh trên dùng mock provider để không gọi dịch vụ LLM bên ngoài. Vì vậy judge metric trong lần chạy này dùng đường fallback của evaluator; Ragas được bỏ qua theo cấu hình mặc định.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Baseline cần có thể chạy lại khi không thể truy cập Crossref hoặc Hugging Face Hub.
- **Các phương án đã cân nhắc:** Luôn tải dữ liệu/model mới khi chạy; hoặc dùng raw snapshot và model snapshot đã cache, chỉ refresh khi bật cấu hình tương ứng.
- **Phương án đã chọn:** Dùng raw snapshot mặc định và model snapshot cục bộ; cho phép refresh nguồn qua cấu hình, đồng thời vẫn giữ model loading theo tên chuẩn khi cache chưa có.
- **Lý do:** Snapshot làm đầu vào tái lập được và tránh lỗi mạng trong lần chạy offline. Chi phí là dữ liệu/model sẽ không tự cập nhật nếu không bật refresh hoặc tải model trước.
- **Bằng chứng:** Baseline chạy với 24 records, GX `success = true`, 24 vectors và `retrieval_hit_rate = 1.0`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi:** `'[WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions'` khi Sentence Transformers yêu cầu Hugging Face Hub.
- **Lệnh hoặc bước tái hiện:** Chạy `script/run_phase1.py` khi model chưa có trong cache và network bị chặn.
- **Nguyên nhân gốc:** Model chưa được cache trong lần đầu; sau khi cache model, thư viện vẫn thử lấy metadata Hub thay vì chỉ dùng snapshot cục bộ.
- **Cách xử lý:** Tải model vào `.model-cache`, đặt đây làm cache mặc định của project và mở trực tiếp snapshot đã cache trong `_load_model()`.
- **Cách xác minh sau khi sửa:** Chạy lại pipeline với `HF_HUB_OFFLINE=1`; pipeline kết thúc exit code 0, tạo 24 vectors và ghi baseline report.
- **Điều học được:** Offline fallback cần kiểm tra không chỉ việc có file model mà cả đường đi mà thư viện dùng để resolve model; cache và snapshot phải được xác minh bằng một lần chạy end-to-end.

## 7. Hiểu biết về luồng end-to-end

1. Pipeline đọc raw records đã parse từ Crossref, cleaning chuẩn hóa trường và tạo `text_for_embedding`; MiniLM biến mỗi văn bản thành vector và Chroma lưu vector cùng metadata theo `paper_id`.
2. Benchmark gồm 5 câu hỏi thuộc các loại summary, authors, date, category và multi-hop. Mỗi câu có ground-truth document IDs. Retrieval hit được tính khi ID trả về giao với tập ID đúng; token F1 so sánh câu trả lời với ground truth. Judge metric bổ sung đánh giá câu trả lời, nhưng lần chạy này dùng mock/fallback.
3. GX kiểm tra cấu trúc và tính hợp lệ của dataset như số dòng, null, trùng `paper_id` và độ dài summary. Freshness theo dõi tuổi hồ sơ; SLA hiện dùng ngưỡng 180 ngày và cho phép tối đa 25% hồ sơ quá hạn.
4. Baseline, corrupted và repaired phải dùng cùng evaluation set để thay đổi metric phản ánh thay đổi dữ liệu thay vì thay đổi câu hỏi hoặc ground truth.
5. Repair chỉ được kết luận thành công khi có artifacts repaired, quality/freshness được chạy lại và metrics repaired được so sánh trên cùng test set. Các artifacts corruption/repair chưa có trong repository tại thời điểm lập báo cáo này, nên chưa thể kết luận repair thành công.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.000 | Chưa có artifact | Chưa có artifact | Baseline tìm được ít nhất một ground-truth document cho cả 5 câu hỏi. |
| `mean_token_f1` | 0.7073 | Chưa có artifact | Chưa có artifact | Kết quả baseline; lần chạy dùng mock/fallback judge path. |
| `judge_accuracy` | 0.600 | Chưa có artifact | Chưa có artifact | Không xem đây là đánh giá từ Gemini vì provider được đặt là `mock`. |
| `mean_judge_score` | 3.400 | Chưa có artifact | Chưa có artifact | Cùng giới hạn mock/fallback như trên. |
| Quality checks | PASS | Chưa có artifact | Chưa có artifact | Baseline GX report có `success = true`. |
| Freshness status | Fresh: 0/24 stale | Chưa có artifact | Chưa có artifact | Baseline report có `is_fresh = true`. |

### Kết luận từ số liệu

1. **Corruption → quality/freshness → agent metric:** Chưa thể lập chuỗi bằng chứng vì `corruption_log.json` và corrupted metrics chưa được tạo.
2. **Repair → quality/freshness → agent metric:** Chưa thể lập chuỗi bằng chứng vì repaired artifacts và repaired metrics chưa được tạo.

Chưa thể xác định corruption nào ảnh hưởng rõ nhất hoặc kết quả nào khác kỳ vọng; cần chạy corruption flow và so sánh trên cùng test set trước khi đưa ra kết luận. Trong repository, `src/pipelines/corruption_flow.py` và `src/ingestion/corruption.py` vẫn là TODO, nên đây là phần còn thiếu chứ không phải kết quả đã xác minh.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Một pipeline có thể tái lập cần lưu raw snapshot, xác định rõ contract của clean data và ghi artifacts theo đường dẫn cấu hình.
2. Quality gate và freshness đo hai khía cạnh khác nhau: dữ liệu có đúng schema/chất lượng tối thiểu không, và dữ liệu có còn mới theo SLA không.
3. Retrieval metric phụ thuộc vào chất lượng dữ liệu và ground-truth IDs; vì vậy cần giữ nguyên benchmark khi so sánh baseline với dữ liệu lỗi và dữ liệu đã repair.

### Nếu có thêm thời gian

Hoàn thiện corruption/repair flow, chạy đủ ba trạng thái trên cùng test set và xuất `corruption_log.json`, quality/freshness reports cùng metrics. Sau đó phân tích mức suy giảm và mức phục hồi theo từng scenario thay vì suy luận từ baseline đơn lẻ.

## 10. Cam kết của thành viên

Các ô dưới đây để tôi tự xác nhận sau khi đọc và kiểm tra lại báo cáo:

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Triều Vương

**Ngày xác nhận:** 2026-09-25
