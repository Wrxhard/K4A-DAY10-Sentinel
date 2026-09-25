# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Văn Huy |
| MSSV | 2A202602428 |
| Khóa/Lớp | K4 |
| Tên nhóm | Sentinel |
| Vai trò chính | RAG Specialist — Vector Index, Retrieval, QA Agent và Benchmark Test Set |
| Repository | [K4A-DAY10-Sentinel](https://github.com/Wrxhard/K4A-DAY10-Sentinel.git) |
| Pull request | [PR #3 — Complete Chroma vector index and benchmark test set](https://github.com/Wrxhard/K4A-DAY10-Sentinel/pull/3) |
| Ngày hoàn thành | 25/09/2026 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Benchmark Test Set | `src/evaluation/testset.py`: `build_test_set()`, `load_or_create_test_set()` | `data/clean/papers_clean.json` gồm 24 paper sạch | `data/eval/test_set.json` gồm 5 câu hỏi thuộc 5 loại | Hoàn thành và kiểm thử |
| Vector index | `src/retrieval/index.py`: `LocalEmbeddingIndex.build_from_clean()`, `semantic_search()` và metadata fallback | `text_for_embedding` và metadata trong clean dataset | Collection ChromaDB `papers-baseline`, 24 documents | Hoàn thành và kiểm thử với MiniLM thật |
| Embedding/index artifact | `data/embeddings/papers_embeddings.json`, `data/chroma/` | Model `sentence-transformers/all-MiniLM-L6-v2` | Manifest embedding và persistent Chroma index | Hoàn thành |
| QA Agent compatibility | `src/retrieval/agent.py`: `run_agent_question()` | Content blocks trả về từ Gemini | Câu trả lời dạng chuỗi sạch | Hoàn thành và kiểm thử với Gemini Flash |
| Cấu hình tương thích CP2 | `src/core/config.py`, `.env.example`, `src/evaluation/__init__.py` | Contract của starter repo và lệnh nghiệm thu CP2 | Alias đường dẫn/API và model mặc định hợp lệ | Hoàn thành |

Tôi chỉ nhận ownership đối với Checkpoint 2 và các thay đổi trực tiếp trong hai commit `a37bd7c`, `d87dd6e`. Tôi không nhận ownership đối với ingestion, cleaning, Great Expectations, corruption flow hoặc repair pipeline.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Kiểm tra contract dữ liệu sạch trước khi index | Cleaning/Data Foundation | Xác nhận 24 dòng, không thiếu `paper_id`, không thiếu `text_for_embedding`, không trùng ID |
| Bổ sung taxonomy fallback | Retrieval và Evaluation | Khắc phục tình trạng 24/24 Crossref records không có subject/category; benchmark và QA dùng cùng quy tắc |
| Đồng bộ API nghiệm thu với starter repo | Pipeline integration | Giữ API `build()`/`search()` cũ, đồng thời thêm `build_from_clean()`/`semantic_search()` để không phá module phụ thuộc |
| Kiểm thử LLM provider | QA Agent | Xác minh Google API key hoạt động với Gemini Flash hiện hành và cập nhật model cấu hình |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Tạo benchmark deterministic | `src/evaluation/testset.py` | 5 samples: `summary`, `authors`, `date`, `category`, `multi_hop` | Lệnh nghiệm thu in `Test set gồm 5 câu hỏi` |
| Kiểm tra ground truth | `data/eval/test_set.json` | Tất cả ground truth không rỗng; multi-hop tham chiếu 2 document IDs hợp lệ | Đối chiếu IDs với `paper_id` trong clean dataset |
| Build MiniLM embeddings | `src/retrieval/embeddings.py`, `data/embeddings/papers_embeddings.json` | Vector 384 chiều cho 24 documents | Encode smoke test và đọc manifest |
| Persist Chroma index | `data/chroma/`, collection `papers-baseline` | Collection có 24 documents và load lại được từ disk | `collection.count() == 24` sau khi mở lại |
| Smoke test retrieval | `LocalEmbeddingIndex.semantic_search()` | Truy vấn `machine learning`, `top_k=2` trả đúng 2 kết quả | Lệnh kiểm thử CP2 |
| Smoke test Gemini QA Agent | `src/retrieval/agent.py` | Agent dùng tool corpus và trả đúng ba tác giả của paper được hỏi | Gemini Flash QA smoke test |

Output chính của tôi là một benchmark có ground truth truy vết được về paper ID và một persistent vector index gồm 24 tài liệu. Các artifact này là đầu vào trực tiếp cho bước baseline evaluation và phép so sánh baseline/corrupted/repaired của nhóm.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Checkpoint 2 cần biến dữ liệu paper đã làm sạch thành không gian vector có thể truy vấn ngữ nghĩa, đồng thời tạo một bộ câu hỏi chuẩn để đo retrieval và answer quality. Hai phần phải dùng chung định danh `paper_id`; nếu benchmark tham chiếu sai ID hoặc test set bị thay đổi giữa các lần chạy thì các metric sau đó không còn khả năng so sánh.

Starter repo và lệnh nghiệm thu còn khác nhau về tên API. Repo dùng `eval_testset`, `build()`, `search()`, trong khi lệnh CP2 dùng `test_set_json`, `build_from_clean()`, `semantic_search()`. Tôi bổ sung lớp tương thích thay vì xóa API cũ để các module evaluation và pipeline hiện có tiếp tục hoạt động.

### Cách triển khai

1. Kiểm tra clean dataframe có đủ cột bắt buộc và tối thiểu 5 paper.
2. Sắp xếp paper theo `published` và `paper_id` để lựa chọn mẫu có tính tái lập.
3. Sinh 5 câu hỏi thuộc 5 loại. Các câu single-hop có một `ground_truth_doc_ids`; câu multi-hop có hai IDs.
4. Giữ đồng thời `type` theo đề CP2 và `question_type` theo evaluator của repo.
5. Nếu artifact cũ sai schema hoặc thiếu loại câu hỏi, `load_or_create_test_set()` tự build lại; nếu hợp lệ thì tái sử dụng.
6. Dùng `all-MiniLM-L6-v2` để encode `text_for_embedding` thành vector 384 chiều và lưu trong ChromaDB collection `papers-baseline` với cosine distance.
7. Lưu manifest chứa model, collection và documents để có thể load index ở tiến trình khác.
8. Vì Crossref snapshot không có category ở cả 24 records, dùng taxonomy deterministic dựa trên title + summary. Benchmark và Chroma metadata gọi cùng một helper để tránh lệch ground truth.
9. Chuẩn hóa content blocks của Gemini thành chuỗi trong `run_agent_question()`.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | `papers_clean.json`; bắt buộc có `paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `published`, `text_for_embedding` |
| Output benchmark | Danh sách JSON với `id`, `type`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids` |
| Output vector | Collection `papers-baseline`, manifest `papers_embeddings.json`, persistent files trong `data/chroma/` |
| Module phụ thuộc | Cleaning/Data Foundation phải tạo clean schema ổn định và document IDs không trùng |
| Module sử dụng output | `retrieval.qa`, `retrieval.agent`, `evaluation.metrics`, baseline/corruption pipelines |
| Điều kiện lỗi cần xử lý | Thiếu cột, ít hơn 5 records, ground truth rỗng, category nguồn trống, model download timeout, collection chưa tồn tại, Gemini trả content blocks |

### Cách xác minh

```powershell
uv run python -c "from core.config import load_settings; from evaluation.testset import load_or_create_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=load_or_create_test_set(df, s.paths.test_set_json); print(f'Tín hiệu hoàn thành: Test set gồm {len(ts.samples)} câu hỏi')"

uv run python -c "from core.config import load_settings; from retrieval.index import LocalEmbeddingIndex; s=load_settings(); idx=LocalEmbeddingIndex(s, collection_name='papers-baseline'); idx.build_from_clean(); res=idx.semantic_search('machine learning', top_k=2); print(f'Tín hiệu hoàn thành: Tìm thấy {len(res)} tài liệu liên quan'); print(idx.collection.count())"
```

- **Kết quả mong đợi:** 5 benchmark samples; 2 retrieval results; collection có 24 documents.
- **Kết quả thực tế:** Đạt đủ ba điều kiện; persistent reload cũng trả `collection_count = 24`.
- **Artifact/log:** `data/eval/test_set.json`, `data/embeddings/papers_embeddings.json`, `data/chroma/`. Không lưu API key trong artifact hoặc Git.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Contract của lệnh CP2 khác contract của starter repo, trong khi các module khác đã gọi API hiện hữu.
- **Các phương án đã cân nhắc:** (1) đổi hẳn API cũ theo lệnh CP2; (2) bỏ qua lệnh CP2 và chỉ giữ API repo; (3) bổ sung adapter tương thích hai chiều.
- **Phương án đã chọn:** Giữ `build()`/`search()` và bổ sung `build_from_clean()`/`semantic_search()`, đồng thời thêm alias `test_set_json` cho `eval_testset`.
- **Lý do:** Phương án này đáp ứng lệnh nghiệm thu nhưng không phá `evaluation.metrics`, QA hoặc pipeline đang phụ thuộc API cũ. Chi phí là một lớp adapter nhỏ, đổi lại giảm rủi ro tích hợp.
- **Bằng chứng quyết định phù hợp:** Cả lệnh checkpoint và smoke test theo API gốc đều chạy; index load lại từ manifest và collection có đủ 24 documents.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** MiniLM không load được do `httpx.ReadTimeout`/kết nối đóng trước khi tải đủ model; Gemini trả `404 NOT_FOUND` cho `gemini-2.5-flash`.
- **Lệnh hoặc bước tái hiện:** Khởi tạo `SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')` và gọi QA Agent với cấu hình Gemini cũ.
- **Nguyên nhân gốc:** Timeout tải mặc định quá ngắn đối với kết nối Hugging Face; model Gemini cũ không còn được Google cấp cho tài khoản mới.
- **Cách xử lý:** Tăng `HF_HUB_DOWNLOAD_TIMEOUT`, tắt Xet cho lần tải, sau đó chạy offline từ cache; chuyển cấu hình sang Gemini Flash được API hỗ trợ. Không thay đổi hoặc commit API key.
- **Cách xác minh sau khi sửa:** MiniLM load thành công, vector có 384 chiều; Chroma chứa 24 documents; Gemini Agent gọi tool và trả đúng ba tác giả.
- **Điều học được:** Cần phân biệt lỗi code với lỗi external dependency. Một smoke test bằng mock xác minh logic tích hợp, nhưng chỉ kiểm thử với model/API thật mới đủ bằng chứng nghiệm thu end-to-end.

## 7. Hiểu biết về luồng end-to-end

1. Crossref response được lưu nguyên trạng để bảo toàn lineage, sau đó parse thành records. Cleaning chuẩn hóa text, ngày, authors/categories, khử trùng và tạo `text_for_embedding`. MiniLM chuyển trường này thành vector và ChromaDB lưu vector cùng metadata theo `paper_id`.
2. Evaluation set chứa câu hỏi, đáp án chuẩn và `ground_truth_doc_ids`. Retrieval hit khi top-k có ít nhất một ID chuẩn. Câu trả lời được so với `ground_truth` bằng Token F1 và LLM Judge. Với multi-hop, danh sách ID cho biết nhiều tài liệu cần được truy xuất.
3. Quality checks kiểm tra tính hợp lệ như row count, null, uniqueness và độ dài. Freshness monitoring đo tuổi dữ liệu và tỷ lệ records vượt SLA 180 ngày. Dữ liệu có thể đúng schema nhưng vẫn stale.
4. Phải dùng cùng test set cho baseline, corrupted và repaired để metric chỉ phản ánh thay đổi của dữ liệu/index, không bị nhiễu do thay đổi câu hỏi hoặc ground truth.
5. Repair thành công khi clean data được tái tạo idempotent từ raw snapshot, quality/freshness trở lại trạng thái đạt, collection repaired được rebuild, và các metric repaired phục hồi gần hoặc bằng baseline trên đúng test set ban đầu.

## 8. Phân tích kết quả

### Metrics chính

Tại thời điểm hoàn thành phần việc CP2, các pipeline baseline, corruption và repair chưa sinh metric artifacts trong `data/results/` hoặc quality reports trong `data/quality/`. Vì vậy tôi không ghi số liệu giả định.

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | Chưa sinh | Chưa sinh | Chưa sinh | Thuộc pha pipeline/evaluation sau CP2 |
| `mean_token_f1` | Chưa sinh | Chưa sinh | Chưa sinh | Cần chạy cùng test set trên cả ba collection |
| `judge_accuracy` | Chưa sinh | Chưa sinh | Chưa sinh | Gemini Agent đã smoke-test, nhưng chưa phải benchmark metric |
| `mean_judge_score` | Chưa sinh | Chưa sinh | Chưa sinh | Không suy diễn từ một câu smoke test |
| Quality checks | Chưa sinh | Chưa sinh | Chưa sinh | Thuộc Observability pipeline |
| Freshness status | Chưa sinh | Chưa sinh | Chưa sinh | Thuộc Observability pipeline |

### Kết luận từ số liệu

Chưa thể hoàn thành chuỗi định lượng corruption → metric degradation → repair recovery vì các artifacts tương ứng chưa tồn tại ở thời điểm viết báo cáo. Phần tôi đã chứng minh định lượng là: clean dataset 24 records → MiniLM vector 384 chiều → Chroma `papers-baseline` 24 documents → truy vấn `top_k=2` trả 2 kết quả → persistent reload giữ nguyên 24 documents.

Một kết quả khác kỳ vọng là Crossref snapshot không có category cho bất kỳ record nào. Tôi kiểm tra trực tiếp và thu được `categories_nonempty = 0`, thay vì tạo ground truth rỗng đã bổ sung taxonomy fallback dùng chung. Ngoài ra Gemini 2.5 Flash không còn khả dụng cho tài khoản mới; kiểm thử API giúp phát hiện và cập nhật cấu hình trước khi tích hợp.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Data contract và document identity quan trọng ngang với model embedding; sai `paper_id` sẽ làm retrieval metric vô nghĩa dù vector search vẫn chạy.
2. Benchmark phải deterministic và bất biến giữa các trạng thái thì phép so sánh mới công bằng và tái lập được.
3. Chất lượng RAG phụ thuộc đồng thời vào metadata, embedding, retrieval và LLM response format; silent failure có thể đến từ category rỗng hoặc provider/model đã hết hỗ trợ.

### Nếu có thêm thời gian

Tôi sẽ bổ sung automated tests cho test-set schema, Chroma persistence và retrieval hit trên các truy vấn cố định; sau đó đánh giá riêng multi-hop retrieval bằng tiêu chí yêu cầu đủ hai ground-truth IDs. Cải thiện được đo bằng test coverage, tỷ lệ multi-hop document recall và khả năng chạy lại hoàn toàn offline sau lần tải model đầu tiên.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact, commit hoặc output kiểm thử để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Văn Huy

**Ngày xác nhận:** 25/09/2026

### Bằng chứng Git

- `a37bd7c` — `feat(cp2): add benchmark and Chroma retrieval workflow`
- `d87dd6e` — `fix(cp2): verify persistent MiniLM index and Gemini agent`
- PR #3 đã merge vào `main` qua commit `bf00adc`.
