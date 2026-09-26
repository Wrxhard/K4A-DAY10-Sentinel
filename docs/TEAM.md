# Danh sách thành viên và phân công nhóm

- **Tên nhóm:** Sentinel
- **Khóa/Lớp:** K4-L3A
- **Repository nộp bài:** https://github.com/Wrxhard/K4A-DAY10-Sentinel

## Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò và module phụ trách | Báo cáo cá nhân |
| ---: | --- | --- | --- | --- | --- |
| 1 | Nguyễn Trọng Phúc | 2A202602552 | Chưa cung cấp | Data Foundation & Quality (CP1, CP2): `crossref.py`, `cleaning.py`, `quality.py`, `testset.py` | Chưa có trong repo |
| 2 | Nguyễn Văn Huy | 2A202602428 | Chưa cung cấp | RAG & Vector Index (CP2): `index.py`, `agent.py`, `embeddings.py` | Chưa có trong repo |
| 3 | Nguyễn Triều Vương (GitHub: Vuog23) | 2A202602422 | Chưa cung cấp | Observability & Baseline Pipeline (CP3): `reporting.py`, `phase1.py` | Chưa có trong repo |
| 4 | Nguyễn Quốc Đạt | 2A202602369 | Chưa cung cấp | Corruption & Repair Integration (CP5): `corruption.py`, `corruption_flow.py` | [report/individual_report.md](../report/individual_report.md) |

## Phân công và kết quả bàn giao

### Nguyễn Trọng Phúc — 2A202602552

- Thu thập dữ liệu từ Crossref và chuẩn hóa dữ liệu sạch qua `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`.
- Phụ trách quality checks và bộ câu hỏi đánh giá trong `src/observability/quality.py`, `src/evaluation/testset.py`.
- Bàn giao dữ liệu trong `data/raw/`, `data/clean/` và báo cáo chất lượng trong `data/quality/`.

### Nguyễn Văn Huy — 2A202602428

- Phụ trách embedding, ChromaDB index và RAG agent qua `src/retrieval/embeddings.py`, `src/retrieval/index.py`, `src/retrieval/agent.py`.
- Phối hợp đánh giá baseline; bàn giao `data/embeddings/` và `data/chroma/`.

### Nguyễn Triều Vương — 2A202602422

- Phụ trách báo cáo observability và baseline pipeline qua `src/observability/reporting.py`, `src/pipelines/phase1.py`.
- Phối hợp đánh giá baseline, theo dõi quality/freshness và lập báo cáo đối chiếu ba trạng thái trong `data/reports/`.

### Nguyễn Quốc Đạt — 2A202602369

- Phụ trách các kịch bản corruption và tích hợp luồng repair qua `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py`.
- Bàn giao `data/results/corruption_log.json`, kết quả corrupted/repaired và phối hợp lập `data/reports/corruption_report.md`.
- Chi tiết phần việc cá nhân: [report/individual_report.md](../report/individual_report.md).

Nguồn phân công: [báo cáo nhóm](../report/group_report.md).
