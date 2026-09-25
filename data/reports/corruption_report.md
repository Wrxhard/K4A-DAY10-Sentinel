# Data Corruption and Repair Report

## Evaluation comparison

| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| `samples` | 5 | 5 | 5 |
| `retrieval_hit_rate` | 1.0 | 0.8 | 1.0 |
| `mean_token_f1` | 0.7072941176470589 | 0.7588235294117647 | 0.7072941176470589 |
| `judge_accuracy` | 0.6 | 0.8 | 0.6 |
| `mean_judge_score` | 3.4 | 3.8 | 3.4 |
| `ragas` | {'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'} | {'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'} | {'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'} |

## Quality and freshness observations

- Corrupted quality checks passed: **False**
- Corrupted freshness: **True**
- Repaired freshness: **True**
