# RW-141-0 Final limitations and risk-response

## Holdout quality result

The frozen untouched holdout contains 20 scenarios: 12 energy and 8 petrochemical.

Overall:
- Recall: 1.00 — PASS
- Precision: 0.142857 — FAIL
- F1: 0.25
- PR-AUC: 0.267857
- ROC-AUC: 0.777778
- Balanced accuracy: 0.666667
- False-positive rate: 0.666667 — FAIL
- p95 API latency: 518.15 ms — PASS

Energy:
- Recall: 1.00
- Precision: 0.166667 — FAIL
- False-positive rate: 1.00 — FAIL

Petrochemical:
- Attack recall: 0.00 — FAIL
- False-positive rate: 0.25 — FAIL

## Limitations

1. The current model is not production-ready against the mandatory precision/FPR gates.
2. Petrochemical ransomware detection does not satisfy the required recall gate on this holdout.
3. The canonical API does not currently expose incident stage, full timeline, localization, affected/suspected assets, propagation path, or full recovery context, so those Stage 14 metrics cannot honestly be reported.
4. Cold/warm memory was not measured through the browser-facing API runner.
5. The temporal challenger is unavailable in the current canonical runtime and the calibrated result explicitly excludes it.
6. Holdout results must not be used to tune the current model or thresholds inside this evaluation cycle.

## Risk response

The current cycle remains a defensive synthetic PoC. Failed quality gates are retained as evidence rather than hidden or corrected after observing the holdout.

A future cycle must freeze a new evaluation boundary before changing features, model, calibration, thresholds, or evidence contracts, then evaluate a newly sealed holdout.
