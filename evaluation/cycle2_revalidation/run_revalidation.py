from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = ROOT / "apps" / "ml-services"
sys.path.insert(0, str(ML_ROOT))

MANIFEST_PATH = ML_ROOT / "artifacts" / "ransomware" / "offline" / "split_assignment_manifest.json"
OUT_DIR = ROOT / "evaluation" / "cycle2_revalidation"
RESULTS_PATH = OUT_DIR / "results.json"
SCORECARD_PATH = OUT_DIR / "scorecard.json"
PACKAGE_PATH = OUT_DIR / "evaluation_package.json"

from config.ransomware.catboost_trainer import load_and_verify_scenarios
from config.ransomware.rw1006_internal_api_cycle2 import app


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
    tnr = tn / (tn + fp) if tn + fp else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0

    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "balanced_accuracy": (recall + tnr) / 2.0,
        "false_positive_rate": fpr,
    }


def calibration_metrics(y_true, probs):
    if not y_true:
        return None

    clipped = [min(max(p, 1e-15), 1 - 1e-15) for p in probs]

    brier = sum(
        (p - y) ** 2 for p, y in zip(clipped, y_true)
    ) / len(y_true)

    log_loss = -sum(
        y * math.log(p) + (1 - y) * math.log(1 - p)
        for y, p in zip(y_true, clipped)
    ) / len(y_true)

    ece = 0.0
    for i in range(10):
        lo = i / 10
        hi = (i + 1) / 10

        rows = [
            (y, p)
            for y, p in zip(y_true, clipped)
            if (lo <= p < hi) or (hi == 1.0 and lo <= p <= hi)
        ]

        if rows:
            confidence = sum(p for _, p in rows) / len(rows)
            empirical_rate = sum(y for y, _ in rows) / len(rows)
            ece += (len(rows) / len(y_true)) * abs(
                confidence - empirical_rate
            )

    return {
        "brier_score": brier,
        "log_loss": log_loss,
        "ece": ece,
    }


def percentile(values, q):
    if not values:
        return None

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    k = (len(values) - 1) * q
    lo = math.floor(k)
    hi = math.ceil(k)

    if lo == hi:
        return values[lo]

    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )

    manifest_hash = sha256_bytes(
        MANIFEST_PATH.read_bytes()
    )

    evaluation_rows = [
        row
        for row in manifest["assignments"]
        if row["split"] == "test"
    ]

    if len(evaluation_rows) != 14:
        raise SystemExit(
            f"Expected 14 Cycle-2 test scenarios, found {len(evaluation_rows)}"
        )

    scenario_ids = [
        row["scenario_id"]
        for row in evaluation_rows
    ]

    if len(scenario_ids) != len(set(scenario_ids)):
        raise SystemExit(
            "Cycle-2 test partition contains duplicate scenario IDs"
        )

    _, frozen = load_and_verify_scenarios()

    frozen_by_id = {
        scenario.scenario_id: scenario
        for scenario in frozen
    }

    client = TestClient(app)

    health = client.get("/health")
    health.raise_for_status()

    started = datetime.now(timezone.utc).isoformat()

    results = []

    for idx, assignment in enumerate(
        evaluation_rows,
        start=1,
    ):
        scenario_id = assignment["scenario_id"]

        scenario = frozen_by_id.get(scenario_id)

        if scenario is None:
            raise RuntimeError(
                f"Frozen scenario missing: {scenario_id}"
            )

        industry = assignment["industry"]

        site_types = sorted(
            scenario.site_types
        )

        site_type = site_types[0]

        site_id = getattr(
            scenario,
            "site_id",
            None,
        )

        if site_id is None:
            site_id = (
                "synthetic-energy-001"
                if industry == "energy"
                else "synthetic-petrochemical-001"
            )

        request = {
            "schema_version": "1.0",
            "mode": "synthetic_scenario",
            "industry": industry,
            "site_id": site_id,
            "site_type": site_type,
            "scenario_id": scenario_id,
            "observable_input": {},
        }

        t0 = time.perf_counter()

        try:
            response = client.post(
                "/internal/ransomware/infer",
                json=request,
            )

            elapsed_ms = (
                time.perf_counter() - t0
            ) * 1000.0

            response.raise_for_status()

            payload = response.json()

            result = payload["result"]

            calibrated = safe_float(
                result
                .get("probabilities", {})
                .get("calibrated")
            )

            decision = result.get(
                "decision",
                "unavailable",
            )

            predicted_attack = (
                decision
                in {"investigate", "high_risk"}
            )

            runtime_contract = result.get(
                "runtime_contract",
                {},
            )

            results.append(
                {
                    "ordinal": idx,
                    "scenario_id": scenario_id,
                    "industry": industry,
                    "site_id": site_id,
                    "site_type": site_type,
                    "use_case_id": assignment["use_case_id"],
                    "variant": assignment["variant"],
                    "truth_attack": (
                        assignment["variant"]
                        == "attack"
                    ),
                    "scored": (
                        calibrated is not None
                        and decision != "unavailable"
                    ),
                    "predicted_attack": predicted_attack,
                    "decision": decision,
                    "calibrated_probability": (
                        calibrated
                        if calibrated is not None
                        else 0.0
                    ),
                    "bundle_version": payload.get(
                        "bundle_version"
                    ),
                    "runtime_contract": runtime_contract,
                    "endpoint_latency_ms": elapsed_ms,
                    "response": payload,
                }
            )

            print(
                f"[{idx:02d}/14] "
                f"{industry:14s} "
                f"{scenario_id} "
                f"truth={assignment['variant']:7s} "
                f"decision={decision:11s} "
                f"p={calibrated:.6f} "
                f"latency={elapsed_ms:.1f}ms"
            )

        except Exception as exc:
            elapsed_ms = (
                time.perf_counter() - t0
            ) * 1000.0

            results.append(
                {
                    "ordinal": idx,
                    "scenario_id": scenario_id,
                    "industry": industry,
                    "site_id": site_id,
                    "site_type": site_type,
                    "use_case_id": assignment["use_case_id"],
                    "variant": assignment["variant"],
                    "truth_attack": (
                        assignment["variant"]
                        == "attack"
                    ),
                    "scored": False,
                    "predicted_attack": False,
                    "decision": "unavailable",
                    "calibrated_probability": 0.0,
                    "endpoint_latency_ms": elapsed_ms,
                    "error": repr(exc),
                }
            )

            print(
                f"[{idx:02d}/14] "
                f"{industry:14s} "
                f"{scenario_id} "
                f"ERROR {exc}"
            )

    RESULTS_PATH.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    scored = [
        row
        for row in results
        if row["scored"]
    ]

    y_true = [
        int(row["truth_attack"])
        for row in scored
    ]

    y_score = [
        row["calibrated_probability"]
        for row in scored
    ]

    y_pred = [
        int(row["predicted_attack"])
        for row in scored
    ]

    overall_detection = (
        binary_metrics(
            y_true,
            y_score,
            y_pred,
        )
        if scored
        else None
    )

    overall_calibration = calibration_metrics(
        y_true,
        y_score,
    )

    sector_slices = {}

    for sector in (
        "energy",
        "petrochemical",
    ):
        subset = [
            row
            for row in scored
            if row["industry"] == sector
        ]

        if subset:
            sy = [
                int(row["truth_attack"])
                for row in subset
            ]

            sp = [
                row["calibrated_probability"]
                for row in subset
            ]

            sd = [
                int(row["predicted_attack"])
                for row in subset
            ]

            sector_slices[sector] = {
                "count": len(subset),
                "detection": binary_metrics(
                    sy,
                    sp,
                    sd,
                ),
                "calibration": calibration_metrics(
                    sy,
                    sp,
                ),
            }

        else:
            sector_slices[sector] = {
                "status": "no_scored_rows"
            }

    latencies = [
        row["endpoint_latency_ms"]
        for row in results
    ]

    safety = {
        "real_action_executed_all_false": all(
            row
            .get("runtime_contract", {})
            .get("real_action_executed")
            is False
            for row in scored
        ),
        "human_approval_required_all_true": all(
            row
            .get("runtime_contract", {})
            .get("human_approval_required")
            is True
            for row in scored
        ),
        "operational_state_claimed_all_false": all(
            row
            .get("runtime_contract", {})
            .get("operational_state_claimed")
            is False
            for row in scored
        ),
        "physical_safety_determination_all_not_determined": all(
            row
            .get("runtime_contract", {})
            .get("physical_safety_determination")
            == "not_determined"
            for row in scored
        ),
    }

    p95_latency = percentile(
        latencies,
        0.95,
    )

    scorecard = {
        "task": "RW-CYCLE2-REVALIDATION",
        "status": (
            "complete"
            if len(results) == 14
            else "incomplete"
        ),
        "evaluation_set": "test",
        "evaluation_set_description": (
            "Pre-existing held-out test partition; "
            "independent of train/validation/calibration. "
            "Not claimed as a newly generated untouched holdout."
        ),
        "original_20_scenario_holdout_preserved": True,
        "manifest_sha256": manifest_hash,
        "scenario_count": len(results),
        "scored_count": len(scored),
        "failed_count": (
            len(results) - len(scored)
        ),
        "overall": {
            "detection": overall_detection,
            "calibration": overall_calibration,
        },
        "sector_slices": sector_slices,
        "runtime": {
            "endpoint_latency_ms": {
                "p50": percentile(
                    latencies,
                    0.50,
                ),
                "p95": p95_latency,
                "min": (
                    min(latencies)
                    if latencies
                    else None
                ),
                "max": (
                    max(latencies)
                    if latencies
                    else None
                ),
            },
            "timeout_or_error_rate": (
                (
                    len(results)
                    - len(scored)
                )
                / len(results)
                if results
                else None
            ),
        },
        "progression": {
            "status": "unavailable",
            "reason": (
                "Cycle-2 canonical API does not "
                "expose incident_stage/timeline fields."
            ),
        },
        "localization": {
            "status": "unavailable",
            "reason": (
                "Cycle-2 canonical API does not "
                "expose affected/suspected asset "
                "or propagation-path fields."
            ),
        },
        "safety": safety,
        "core_quality_gate_comparison": {
            "attack_recall_target": 0.90,
            "precision_target": 0.85,
            "non_attack_fpr_target": 0.10,
            "p95_latency_target_ms": 1000.0,
            "attack_recall": (
                overall_detection["recall"]
                if overall_detection
                else None
            ),
            "precision": (
                overall_detection["precision"]
                if overall_detection
                else None
            ),
            "non_attack_fpr": (
                overall_detection[
                    "false_positive_rate"
                ]
                if overall_detection
                else None
            ),
            "p95_latency_ms": p95_latency,
        },
        "limitations": [
            "This is a Cycle-2 revalidation on the pre-existing test partition, not a newly generated untouched holdout.",
            "The original frozen 20-scenario holdout was not modified or rerun.",
            "Progression and localization acceptance metrics remain unavailable from the current canonical API contract.",
        ],
    }

    SCORECARD_PATH.write_text(
        json.dumps(
            scorecard,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    package = {
        "task": "RW-CYCLE2-REVALIDATION",
        "created_at": started,
        "manifest_sha256": manifest_hash,
        "scenario_ids": scenario_ids,
        "scorecard_sha256": sha256_bytes(
            SCORECARD_PATH.read_bytes()
        ),
        "results_sha256": sha256_bytes(
            RESULTS_PATH.read_bytes()
        ),
        "scorecard": scorecard,
    }

    package[
        "evaluation_package_sha256"
    ] = canonical_sha256(package)

    PACKAGE_PATH.write_text(
        json.dumps(
            package,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("RW-CYCLE2-REVALIDATION: COMPLETE")
    print(f"scenarios: {len(results)}")
    print(f"scored: {len(scored)}")
    print(f"scorecard: {SCORECARD_PATH}")
    print(f"results: {RESULTS_PATH}")
    print(
        "package hash: "
        f"{package['evaluation_package_sha256']}"
    )


if __name__ == "__main__":
    main()
