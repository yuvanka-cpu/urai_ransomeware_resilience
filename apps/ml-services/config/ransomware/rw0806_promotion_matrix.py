from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "artifacts" / "ransomware" / "offline"
REPORT = ARTIFACT_DIR / "rw0806_promotion_matrix.json"


def load(name: str) -> dict:
    with (ARTIFACT_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    tabpfn = load("rw0801_tabpfn_challenger_report.json")
    tcn = load("rw0802_tcn_report.json")
    transformer = load("rw0803_transformer_report.json")
    graph = load("rw0805_graph_challenger_report.json")

    report = {
        "task": "RW-080-6",
        "status": "PASS",
        "comparison_scope": "stage_8_challengers",
        "seed": 20260921,
        "synthetic_only": True,
        "real_action_executed": False,
        "final_holdout_used": False,
        "promotion_rule": (
            "Promote only when challenger evidence demonstrates meaningful "
            "improvement over simpler baselines under the frozen evaluation "
            "contract, with calibration, robustness, runtime, explanation, "
            "and sector-specific evidence."
        ),
        "evidence_limits": [
            "Current challenger reports are not untouched-final-holdout evidence.",
            "Calibration metrics are not present in the challenger reports.",
            "p50/p95 latency and memory measurements are not present in these challenger reports.",
            "GraphSAGE/GATv2 results are controlled structural benchmarks over the two canonical sector graphs.",
            "Therefore no challenger is promoted from RW-080-6."
        ],
        "challengers": {
            "tabpfn_v3_5": {
                "evidence_id": "RW-080-1",
                "quality": tabpfn["metrics"],
                "robustness": "scenario_group_leakage_excluded",
                "calibration": "not_measured",
                "runtime_memory": "not_measured_in_stage_8_report",
                "explanation": "feature-contract based; no challenger-specific explanation evidence",
                "energy": "not_separately_reported",
                "petrochemical": "not_separately_reported",
                "promotion": "REJECT",
                "reason": (
                    "Validation quality is modest (recall 0.1667, F1 0.25, "
                    "balanced accuracy 0.5167) and required calibration, "
                    "runtime, memory, and sector-specific holdout evidence are absent."
                )
            },
            "tcn": {
                "evidence_id": "RW-080-2",
                "quality": {
                    "attack_detection_rate": tcn["metrics"]["attack_detection_rate"],
                    "mean_detection_delay_timesteps": tcn["metrics"]["mean_detection_delay_timesteps"],
                    "stage_recall": tcn["metrics"]["stage_recall"],
                },
                "robustness": "scenario_boundary_crossing=false",
                "calibration": "not_measured",
                "runtime_memory": "not_measured_in_stage_8_report",
                "explanation": "causal temporal architecture with observable-only inputs",
                "energy": "not_separately_reported",
                "petrochemical": "not_separately_reported",
                "promotion": "REJECT",
                "reason": (
                    "All 8 validation attack scenarios were detected, but mean "
                    "detection delay was 7 timesteps and early-stage recall was "
                    "0.0 for initial access through recovery impairment. "
                    "Required final-holdout and calibration evidence is absent."
                )
            },
            "compact_transformer": {
                "evidence_id": "RW-080-3",
                "quality": {
                    "attack_detection_rate": transformer["metrics"]["attack_detection_rate"],
                    "mean_detection_delay_timesteps": transformer["metrics"]["mean_detection_delay_timesteps"],
                    "false_positive_scenario_count": transformer["metrics"]["false_positive_scenario_count"],
                },
                "robustness": "scenario_boundary_crossing=false",
                "calibration": "not_measured",
                "runtime_memory": "not_measured_in_stage_8_report",
                "explanation": "attention-based sequence representation; no independent explanation evidence",
                "energy": "not_separately_reported",
                "petrochemical": "not_separately_reported",
                "promotion": "REJECT",
                "reason": (
                    "The model detected all 8 validation attacks at timestep 0, "
                    "but produced one false-positive fault scenario. The result "
                    "also requires final-holdout and calibration validation before promotion."
                )
            },
            "graphsage": {
                "evidence_id": "RW-080-5",
                "quality": graph["results"],
                "robustness": "unseen-node and held-out-topology tests executed",
                "calibration": "not_measured",
                "runtime_memory": "not_measured_in_stage_8_report",
                "explanation": "graph structure and propagation paths are inspectable",
                "energy": "controlled_structural_benchmark_only",
                "petrochemical": "controlled_structural_benchmark_only",
                "promotion": "REJECT",
                "reason": (
                    "GraphSAGE achieved strong structural localization values, "
                    "but the benchmark uses only the two canonical sector graphs "
                    "and final_holdout_used=false. Unseen-node ranking also placed "
                    "the held-out node last despite a high raw score, so production "
                    "localization superiority is not established."
                )
            },
            "gatv2": {
                "evidence_id": "RW-080-5",
                "quality": graph["results"],
                "robustness": "unseen-node and held-out-topology tests executed",
                "calibration": "not_measured",
                "runtime_memory": "not_measured_in_stage_8_report",
                "explanation": "attention-based graph representation; structural paths remain inspectable",
                "energy": "controlled_structural_benchmark_only",
                "petrochemical": "controlled_structural_benchmark_only",
                "promotion": "REJECT",
                "reason": (
                    "GATv2 passed the structural benchmark but the benchmark is "
                    "too small for promotion, with final_holdout_used=false and "
                    "limited unseen-node ranking evidence."
                )
            }
        },
        "retained_baseline": {
            "graph_method": "deterministic_weighted_graph_propagation",
            "status": "RETAIN_AS_AUDITABLE_GRAPH_BASELINE",
            "reason": (
                "Deterministic propagation remains directly auditable and "
                "provides explicit edge types, paths, and bounded propagation "
                "without requiring learned graph-model claims."
            )
        },
        "next_evidence_required": [
            "Untouched final holdout evaluated once after contracts and thresholds are frozen.",
            "Energy and petrochemical scorecards reported separately.",
            "Brier score, log loss, reliability diagram, and expected calibration error.",
            "p50/p95 latency, memory, cold/warm load, timeout/error rate.",
            "Critical-service recall and IT-to-OT path plausibility for graph evaluation.",
            "Promotion only after meaningful improvement over the simpler baseline is demonstrated."
        ]
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("RW-080-6: PASS")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
