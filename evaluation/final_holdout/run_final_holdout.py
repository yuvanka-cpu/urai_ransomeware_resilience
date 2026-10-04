from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = ROOT / "apps" / "ml-services"
sys.path.insert(0, str(ML_ROOT))

MANIFEST_PATH = ML_ROOT / "artifacts" / "ransomware" / "offline" / "split_assignment_manifest.json"
OUT_DIR = ROOT / "evaluation" / "final_holdout"
LOCK_PATH = OUT_DIR / "FINAL_HOLDOUT_LOCK.json"
RESULTS_PATH = OUT_DIR / "results.json"
SCORECARD_PATH = OUT_DIR / "scorecard.json"
PACKAGE_PATH = OUT_DIR / "evaluation_package.json"

API_URL = "http://127.0.0.1:8000/api/v1/ransomware/infer"
HEALTH_URL = "http://127.0.0.1:8000/health"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(obj) -> str:
    return sha256_bytes(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


def safe_float(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def binary_metrics(y_true, y_score, y_pred):
    tp = sum(a == 1 and b == 1 for a, b in zip(y_true, y_pred))
    tn = sum(a == 0 and b == 0 for a, b in zip(y_true, y_pred))
    fp = sum(a == 0 and b == 1 for a, b in zip(y_true, y_pred))
    fn = sum(a == 1 and b == 0 for a, b in zip(y_true, y_pred))

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    tpr = recall
    tnr = tn / (tn + fp) if tn + fp else 0.0
    balanced_accuracy = (tpr + tnr) / 2.0
    fpr = fp / (fp + tn) if fp + tn else 0.0

    # Rank-based ROC-AUC.
    positives = [(s, y) for s, y in zip(y_score, y_true) if y == 1]
    negatives = [(s, y) for s, y in zip(y_score, y_true) if y == 0]
    roc_auc = None
    if positives and negatives:
        wins = ties = 0
        for ps, _ in positives:
            for ns, _ in negatives:
                if ps > ns:
                    wins += 1
                elif ps == ns:
                    ties += 1
        roc_auc = (wins + 0.5 * ties) / (len(positives) * len(negatives))

    # Average precision / PR-AUC.
    ranked = sorted(zip(y_score, y_true), key=lambda x: x[0], reverse=True)
    pos_total = sum(y_true)
    pr_auc = None
    if pos_total:
        tp_running = 0
        prev_recall = 0.0
        area = 0.0
        for idx, (_, label) in enumerate(ranked, start=1):
            if label == 1:
                tp_running += 1
                recall_at_k = tp_running / pos_total
                precision_at_k = tp_running / idx
                area += precision_at_k * (recall_at_k - prev_recall)
                prev_recall = recall_at_k
        pr_auc = area

    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "balanced_accuracy": balanced_accuracy,
        "false_positive_rate": fpr,
    }


def calibration_metrics(y_true, probs):
    clipped = [min(max(p, 1e-15), 1 - 1e-15) for p in probs]
    brier = sum((p - y) ** 2 for p, y in zip(clipped, y_true)) / len(y_true)
    log_loss = -sum(
        y * math.log(p) + (1 - y) * math.log(1 - p)
        for y, p in zip(y_true, clipped)
    ) / len(y_true)

    bins = []
    for lower in [i / 10 for i in range(10)]:
        upper = lower + 0.1
        rows = [
            (y, p)
            for y, p in zip(y_true, clipped)
            if (lower <= p < upper) or (upper == 1.0 and p <= upper and p >= lower)
        ]
        if rows:
            conf = sum(p for _, p in rows) / len(rows)
            acc = sum(y for y, _ in rows) / len(rows)
            bins.append({
                "lower": lower,
                "upper": upper,
                "count": len(rows),
                "mean_confidence": conf,
                "empirical_rate": acc,
            })

    ece = sum(
        (b["count"] / len(y_true))
        * abs(b["mean_confidence"] - b["empirical_rate"])
        for b in bins
    )

    return {
        "brier_score": brier,
        "log_loss": log_loss,
        "ece": ece,
        "reliability_bins": bins,
    }


def sector_metrics(rows):
    output = {}
    for sector in ("energy", "petrochemical"):
        subset = [r for r in rows if r["industry"] == sector and r["scored"]]
        if not subset:
            output[sector] = {"status": "no_scored_rows"}
            continue
        y = [r["truth_attack"] for r in subset]
        p = [r["calibrated_probability"] for r in subset]
        pred = [r["predicted_attack"] for r in subset]
        output[sector] = {
            "count": len(subset),
            "detection": binary_metrics(y, p, pred),
            "calibration": calibration_metrics(y, p),
        }
    return output


if LOCK_PATH.exists():
    raise SystemExit(
        f"REFUSING TO RERUN FINAL HOLDOUT: {LOCK_PATH} already exists"
    )

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
manifest_hash = sha256_bytes(MANIFEST_PATH.read_bytes())

holdout = [
    a for a in manifest["assignments"]
    if a["split"] == "untouched_holdout"
]

scenario_ids = [a["scenario_id"] for a in holdout]

if len(holdout) != len(set(scenario_ids)):
    raise SystemExit("Holdout manifest contains duplicate scenario IDs")

if len(holdout) != 20:
    raise SystemExit(f"Expected 20 untouched-holdout scenarios, found {len(holdout)}")

# Build scenario metadata from the frozen canonical loader.
from config.ransomware.catboost_trainer import load_and_verify_scenarios

_, frozen = load_and_verify_scenarios()
frozen_by_id = {s.scenario_id: s for s in frozen}

started = datetime.now(timezone.utc).isoformat()

# Health check happens before the irrevocable run lock.
with httpx.Client(timeout=5.0) as client:
    health = client.get(HEALTH_URL)
    health.raise_for_status()

lock_payload = {
    "run": "RW-140-1",
    "created_at": started,
    "manifest_sha256": manifest_hash,
    "scenario_count": len(holdout),
    "scenario_ids": scenario_ids,
    "exactly_once_policy": True,
}
LOCK_PATH.write_text(json.dumps(lock_payload, indent=2), encoding="utf-8")

results = []

with httpx.Client(timeout=5.0) as client:
    for idx, assignment in enumerate(holdout, start=1):
        scenario_id = assignment["scenario_id"]
        scenario = frozen_by_id.get(scenario_id)

        if scenario is None:
            raise RuntimeError(f"Frozen scenario missing: {scenario_id}")

        industry = assignment["industry"]

        # Canonical site/site-type metadata with deterministic fallback
        site_id = getattr(scenario, "site_id", None)
        site_types = getattr(scenario, "site_types", None)
        site_type = getattr(scenario, "site_type", None)

        if site_type is None and site_types:
            if isinstance(site_types, (list, tuple)):
                site_type = site_types[0]
            else:
                site_type = str(site_types).split("|")[0]

        if site_id is None:
            site_id = (
                "synthetic-energy-001"
                if industry == "energy"
                else "synthetic-petrochemical-001"
            )

        request = {
            "schema_version": "1.0",
            "use_case": "ransomware_resilience",
            "industry": industry,
            "site_id": site_id,
            "site_type": site_type,
            "scenario_id": scenario_id,
            "observable_input": {},
        }

        t0 = time.perf_counter()
        try:
            response = client.post(API_URL, json=request)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            response.raise_for_status()
            payload = response.json()

            model_result = payload.get("result", payload)
            probabilities = model_result.get("probabilities", {})
            decision = model_result.get("decision", "unavailable")

            calibrated = safe_float(probabilities.get("calibrated"))
            predicted_attack = decision in {"investigate", "high_risk"}

            results.append({
                "ordinal": idx,
                "scenario_id": scenario_id,
                "industry": industry,
                "site_id": site_id,
                "site_type": site_type,
                "variant": assignment["variant"],
                "truth_attack": assignment["variant"] == "attack",
                "scored": calibrated is not None and decision != "unavailable",
                "predicted_attack": predicted_attack,
                "decision": decision,
                "calibrated_probability": calibrated if calibrated is not None else 0.0,
                "request_id": model_result.get("request_id") or payload.get("request_id"),
                "trace_id": model_result.get("trace_id") or payload.get("trace_id"),
                "artifact_status": model_result.get("artifact_status"),
                "data_provenance": model_result.get("data_provenance"),
                "runtime_state": model_result.get("runtime_state"),
                "warnings": model_result.get("warnings", []),
                "audit": model_result.get("audit", {}),
                "endpoint_latency_ms": elapsed_ms,
                "response": payload,
            })

            print(
                f"[{idx:02d}/20] {industry:14s} {scenario_id} "
                f"decision={decision:11s} p={calibrated} latency={elapsed_ms:.1f}ms"
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            results.append({
                "ordinal": idx,
                "scenario_id": scenario_id,
                "industry": industry,
                "site_id": site_id,
                "site_type": site_type,
                "variant": assignment["variant"],
                "truth_attack": assignment["variant"] == "attack",
                "scored": False,
                "predicted_attack": False,
                "decision": "unavailable",
                "calibrated_probability": 0.0,
                "endpoint_latency_ms": elapsed_ms,
                "error": repr(exc),
            })
            print(f"[{idx:02d}/20] {industry:14s} {scenario_id} ERROR {exc}")

RESULTS_PATH.write_text(
    json.dumps(results, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

scored = [r for r in results if r["scored"]]

y_true = [int(r["truth_attack"]) for r in scored]
y_score = [r["calibrated_probability"] for r in scored]
y_pred = [int(r["predicted_attack"]) for r in scored]

overall_detection = binary_metrics(y_true, y_score, y_pred) if scored else None
overall_calibration = calibration_metrics(y_true, y_score) if scored else None

latencies = sorted(r["endpoint_latency_ms"] for r in results)

def percentile(values, q):
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    k = (len(values) - 1) * q
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return values[lo]
    return values[lo] + (values[hi] - values[lo]) * (k - lo)

# Current API response contract is known to omit these canonical fields.
missing_canonical_fields = []
if scored:
    sample = scored[0]["response"]
    result = sample.get("result", sample)
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
        if field not in result:
            missing_canonical_fields.append(field)

scorecard = {
    "task": "RW-140",
    "status": "complete" if len(results) == 20 else "incomplete",
    "manifest_sha256": manifest_hash,
    "scenario_count": len(results),
    "scored_count": len(scored),
    "failed_count": len(results) - len(scored),
    "overall": {
        "detection": overall_detection,
        "calibration": overall_calibration,
    },
    "sector_slices": sector_metrics(results),
    "runtime": {
        "endpoint_latency_ms": {
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "min": min(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
        },
        "timeout_or_error_rate": (
            (len(results) - len(scored)) / len(results)
            if results else None
        ),
        "cold_warm_memory": "not measured by frontend-facing API runner",
    },
    "progression": {
        "status": "unavailable",
        "reason": "Current canonical API output does not expose incident_stage/timeline fields.",
    },
    "localization": {
        "status": "unavailable",
        "reason": "Current canonical API output does not expose localization/affected-asset fields.",
    },
    "canonical_contract_gap": {
        "status": "partial",
        "missing_fields_observed": missing_canonical_fields,
    },
    "safety": {
        "real_action_executed_all_false": all(
            (
                r.get("response", {}).get("real_action_executed", False) is False
                and r.get("response", {}).get("result", r.get("response", {})).get(
                    "real_action_executed", False
                ) is False
            )
            for r in results
        ),
        "human_approval_required_all_true": all(
            (
                r.get("response", {}).get("human_approval_required", True) is True
                and r.get("response", {}).get("result", r.get("response", {})).get(
                    "human_approval_required", True
                ) is True
            )
            for r in results
        ),
    },
    "limitations": [
        "Untouched holdout was executed exactly once per scenario through POST /api/v1/ransomware/infer.",
        "Progression/localization metrics remain unavailable because the current canonical API contract does not emit the required fields.",
        "Cold/warm memory was not measured through the browser-facing API runner.",
    ],
}

SCORECARD_PATH.write_text(
    json.dumps(scorecard, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

package = {
    "task": "RW-140-1",
    "run_manifest": lock_payload,
    "scorecard_sha256": sha256_bytes(SCORECARD_PATH.read_bytes()),
    "results_sha256": sha256_bytes(RESULTS_PATH.read_bytes()),
    "scorecard": scorecard,
}

package["evaluation_package_sha256"] = canonical_sha256(package)
PACKAGE_PATH.write_text(
    json.dumps(package, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print()
print("RW-140-1: COMPLETE")
print(f"scenarios: {len(results)}")
print(f"scored: {len(scored)}")
print(f"package hash: {package['evaluation_package_sha256']}")
print(f"scorecard: {SCORECARD_PATH}")
print(f"results: {RESULTS_PATH}")
