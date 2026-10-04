from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evaluation" / "final_holdout"

RESULTS = OUT / "results.json"
LOCK = OUT / "FINAL_HOLDOUT_LOCK.json"
SCORECARD = OUT / "scorecard.json"
PACKAGE = OUT / "evaluation_package.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pct(values, q):
    values = sorted(values)
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    k = (len(values) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return values[lo]
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def metrics(y, score, pred):
    tp = sum(a == 1 and b == 1 for a, b in zip(y, pred))
    tn = sum(a == 0 and b == 0 for a, b in zip(y, pred))
    fp = sum(a == 0 and b == 1 for a, b in zip(y, pred))
    fn = sum(a == 1 and b == 0 for a, b in zip(y, pred))

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )
    specificity = tn / (tn + fp) if tn + fp else 0.0
    balanced = (recall + specificity) / 2
    fpr = fp / (fp + tn) if fp + tn else 0.0

    pos = [(s, yy) for s, yy in zip(score, y) if yy == 1]
    neg = [(s, yy) for s, yy in zip(score, y) if yy == 0]
    roc_auc = None
    if pos and neg:
        wins = ties = 0
        for ps, _ in pos:
            for ns, _ in neg:
                if ps > ns:
                    wins += 1
                elif ps == ns:
                    ties += 1
        roc_auc = (wins + 0.5 * ties) / (len(pos) * len(neg))

    ranked = sorted(zip(score, y), reverse=True)
    positives = sum(y)
    pr_auc = None
    if positives:
        tp_run = 0
        prev_recall = 0.0
        area = 0.0
        for i, (_, yy) in enumerate(ranked, 1):
            if yy == 1:
                tp_run += 1
                recall_k = tp_run / positives
                precision_k = tp_run / i
                area += precision_k * (recall_k - prev_recall)
                prev_recall = recall_k
        pr_auc = area

    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "pr_auc": pr_auc,
        "roc_auc": roc_auc,
        "balanced_accuracy": balanced,
        "false_positive_rate": fpr,
    }


def calibration(y, p):
    clipped = [min(max(float(x), 1e-15), 1 - 1e-15) for x in p]

    brier = sum((pp - yy) ** 2 for yy, pp in zip(y, clipped)) / len(y)
    log_loss = -sum(
        yy * math.log(pp) + (1 - yy) * math.log(1 - pp)
        for yy, pp in zip(y, clipped)
    ) / len(y)

    bins = []
    for i in range(10):
        lo = i / 10
        hi = (i + 1) / 10
        rows = [
            (yy, pp)
            for yy, pp in zip(y, clipped)
            if lo <= pp < hi or (i == 9 and pp == 1.0)
        ]
        if rows:
            conf = sum(pp for _, pp in rows) / len(rows)
            acc = sum(yy for yy, _ in rows) / len(rows)
            bins.append({
                "lower": lo,
                "upper": hi,
                "count": len(rows),
                "mean_confidence": conf,
                "empirical_rate": acc,
            })

    ece = sum(
        (b["count"] / len(y))
        * abs(b["mean_confidence"] - b["empirical_rate"])
        for b in bins
    )

    return {
        "brier_score": brier,
        "log_loss": log_loss,
        "ece": ece,
        "reliability_bins": bins,
    }


if not RESULTS.exists():
    raise SystemExit("results.json not found")

raw = json.loads(RESULTS.read_text(encoding="utf-8"))

if len(raw) != 20:
    raise SystemExit(f"Expected 20 raw holdout rows, found {len(raw)}")

final = []

for row in raw:
    payload = row.get("response")
    if not isinstance(payload, dict):
        raise SystemExit(f"Missing raw response for {row.get('scenario_id')}")

    model = payload.get("model_result")
    if not isinstance(model, dict):
        raise SystemExit(
            f"Missing model_result for {row.get('scenario_id')}"
        )

    probabilities = model.get("probabilities", {})
    calibrated = float(probabilities["calibrated"])
    decision = model["decision"]

    final.append({
        **row,
        "scored": True,
        "decision": decision,
        "predicted_attack": decision in {"investigate", "high_risk"},
        "calibrated_probability": calibrated,
        "catboost_probability": float(probabilities["catboost"]),
        "stacked_probability": float(probabilities["stacked"]),
        "request_id": payload.get("request_id"),
        "trace_id": payload.get("trace_id"),
        "artifact_status": payload.get("artifact_status"),
        "data_provenance": payload.get("data_provenance"),
        "runtime_state": payload.get("runtime_state"),
        "warnings": payload.get("warnings", []),
        "audit": payload.get("audit", {}),
    })

RESULTS.write_text(
    json.dumps(final, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

y = [int(r["truth_attack"]) for r in final]
p = [r["calibrated_probability"] for r in final]
pred = [int(r["predicted_attack"]) for r in final]

sector_slices = {}
for sector in ("energy", "petrochemical"):
    subset = [r for r in final if r["industry"] == sector]
    yy = [int(r["truth_attack"]) for r in subset]
    pp = [r["calibrated_probability"] for r in subset]
    pd = [int(r["predicted_attack"]) for r in subset]
    sector_slices[sector] = {
        "count": len(subset),
        "variant_counts": {
            v: sum(r["variant"] == v for r in subset)
            for v in sorted({r["variant"] for r in subset})
        },
        "detection": metrics(yy, pp, pd),
        "calibration": calibration(yy, pp),
    }

latencies = [float(r["endpoint_latency_ms"]) for r in final]

missing = []
sample_model = final[0]["response"]["model_result"]
for field in (
    "incident_stage",
    "severity",
    "resilience_score",
    "affected_assets",
    "suspected_assets",
    "timeline",
    "propagation_path",
    "backup_readiness",
):
    if field not in sample_model:
        missing.append(field)

scorecard = {
    "task": "RW-140",
    "status": "complete_with_documented_exact_once_exception",
    "run_manifest": json.loads(LOCK.read_text(encoding="utf-8"))
    if LOCK.exists() else None,
    "scenario_count": len(final),
    "scored_count": len(final),
    "failed_count": 0,
    "overall": {
        "detection": metrics(y, p, pred),
        "calibration": calibration(y, p),
    },
    "sector_slices": sector_slices,
    "runtime": {
        "endpoint_latency_ms": {
            "p50": pct(latencies, 0.50),
            "p95": pct(latencies, 0.95),
            "min": min(latencies),
            "max": max(latencies),
        },
        "timeout_or_error_rate": 0.0,
        "cold_warm_memory": "not measured by this API runner",
    },
    "progression": {
        "status": "unavailable",
        "reason": "Current canonical API does not emit incident_stage or timeline.",
    },
    "localization": {
        "status": "unavailable",
        "reason": "Current canonical API does not emit affected/suspected assets or propagation context.",
    },
    "canonical_contract_gap": {
        "status": "partial",
        "missing_fields_observed": missing,
    },
    "safety": {
        "real_action_executed_all_false": all(
            r["response"]["real_action_executed"] is False
            for r in final
        ),
        "human_approval_required_all_true": all(
            r["response"]["human_approval_required"] is True
            for r in final
        ),
    },
    "limitations": [
        "The 20 final-holdout runner requests were completed once each and their raw responses were retained.",
        "One subsequent diagnostic request was made against the first holdout scenario to inspect the response envelope; it is excluded from the final evidence set.",
        "Progression/localization metrics remain unavailable because the canonical API does not emit the required fields.",
        "Cold/warm memory was not measured through the browser-facing API.",
    ],
}

SCORECARD.write_text(
    json.dumps(scorecard, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

package = {
    "task": "RW-140-1",
    "scenario_count": len(final),
    "results_sha256": sha256_bytes(RESULTS.read_bytes()),
    "scorecard_sha256": sha256_bytes(SCORECARD.read_bytes()),
    "scorecard": scorecard,
}

package["evaluation_package_sha256"] = sha256_bytes(
    json.dumps(
        package,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
)

PACKAGE.write_text(
    json.dumps(package, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("RW-140 FINALIZE: PASS")
print("scenarios:", len(final))
print("scored:", len(final))
print("overall detection:", json.dumps(scorecard["overall"]["detection"]))
print("energy:", json.dumps(sector_slices["energy"]["detection"]))
print("petrochemical:", json.dumps(sector_slices["petrochemical"]["detection"]))
print("p50 latency:", scorecard["runtime"]["endpoint_latency_ms"]["p50"])
print("p95 latency:", scorecard["runtime"]["endpoint_latency_ms"]["p95"])
print("evaluation package hash:", package["evaluation_package_sha256"])
