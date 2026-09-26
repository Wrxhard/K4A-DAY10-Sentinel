# Data Corruption and Repair Report

## 1. Bảng đối chiếu 3 trạng thái

### Data Quality Gate & Freshness

| Chỉ số | Baseline | Corrupted | Repaired |
| --- | :---: | :---: | :---: |
| **Data Quality Gate** | ✅ PASSED | ❌ FAILED | ✅ PASSED |
| **Freshness SLA** | ✅ Fresh (0/24 stale) | ❌ Stale (14/24 stale, vi phạm SLA) | ✅ Fresh (0/24 stale) |

### Evaluation Metrics

| Metric | Baseline | Corrupted | Δ Corrupt | Repaired | Δ Repair |
| --- | ---: | ---: | ---: | ---: | ---: |
| `samples` | 5 | 5 | — | 5 | — |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | -0.2000 | 1.0000 | +0.2000 |
| `mean_token_f1` | 0.7073 | 0.5588 | -0.1485 | 0.7073 | +0.1485 |
| `judge_accuracy` | 0.6000 | 0.6000 | — | 0.6000 | — |
| `mean_judge_score` | 3.6000 | 3.6000 | — | 3.6000 | — |

## 2. Phân tích nhân quả

### Chuỗi 1: Corruption → Suy giảm

- **Nguyên nhân:** 6 kịch bản corruption (drop latest, blank summary, inject noise, truncate title, stale date, duplicate rows) được tiêm vào dữ liệu sạch.
- **Tín hiệu observability:** Data Quality Gate chuyển từ ✅ PASSED → ❌ FAILED. Freshness chuyển từ ✅ Fresh (0/24 stale) → ❌ Stale (14/24 stale, vi phạm SLA).
- **Tác động lên RAG Agent:** Retrieval hit rate giảm từ 1.0000 → 0.8000. Dữ liệu bị mất/nhiễu khiến vector index không truy hồi đúng tài liệu ground-truth.

### Chuỗi 2: Repair → Phục hồi

- **Hành động:** Idempotent repair từ raw records (`data/raw/crossref_records.json`), rebuild clean → re-embed → re-index.
- **Tín hiệu observability:** Quality Gate phục hồi → ✅ PASSED. Freshness phục hồi → ✅ Fresh (0/24 stale).
- **Tác động lên RAG Agent:** Retrieval hit rate phục hồi về 1.0000. Toàn bộ metrics trở về mức baseline.

## 3. Kết luận

- Hệ thống Data Observability (GX 1.x + Freshness SLA) **phát hiện thành công** sự suy giảm chất lượng dữ liệu do corruption gây ra.
- Cơ chế Idempotent Repair từ raw snapshot **phục hồi hoàn toàn** chất lượng dữ liệu và hiệu năng RAG Agent.
- Corruption ảnh hưởng rõ nhất: **drop latest records** — trực tiếp làm mất tài liệu ground-truth khỏi vector index.
