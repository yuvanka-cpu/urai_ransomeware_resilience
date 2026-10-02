from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "artifacts" / "ransomware" / "offline"
REPORT = ARTIFACT_DIR / "rw0807_promotion_decision.json"


def load(name: str) -> dict:
    with (ARTIFACT_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    matrix = load("rw0806_promotion_matrix.json")
    tcn = load("rw0802_tcn_report.json")
    transformer = load("rw0803_transformer_report.json")
    graph = load("rw0805_graph_challenger_report.json")

    thresholds = {
        "temporal_detection_delay_improvement_timesteps": 2.0,
        "temporal_stage_recall_improvement_absolute": 0.10,
        "graph_weighted_overlap_improvement_absolute": 0.10,
        "graph_requires_critical_service_localization": True,
        "graph_requires_it_to_ot_path_plausibility": True,
    }

    report = {
        "task": "RW-080-7",
        "status": "PASS",
        "decision": "NO_CHALLENGER_PROMOTED",
        "seed": 20260921,
        "synthetic_only": True,
        "real_action_executed": False,
        "final_holdout_used": False,
        "predeclared_thresholds": thresholds,
        "baseline_policy": (
            "Temporal and graph complexity are rejected unless the challenger "
            "demonstrates the declared meaningful improvement over the simpler "
            "baseline under the frozen evaluation contract."
        ),
        "decisions": {
            "tcn": {
                "promotion": "REJECT",
                "evidence": {
                    "attack_detection_rate":
                        tcn["metrics"]["attack_detection_rate"],
                    "mean_detection_delay_timesteps":
                        tcn["metrics"]["mean_detection_delay_timesteps"],
                    "stage_recall":
                        tcn["metrics"]["stage_recall"],
                },
                "reason": (
                    "No promotion: the available report does not establish the "
                    "required improvement over the engineered-window baseline, "
                    "does not contain untouched-final-holdout evidence, and "
                    "does not provide the required calibration/runtime evidence."
                ),
            },
            "compact_transformer": {
                "promotion": "REJECT",
                "evidence": {
                    "attack_detection_rate":
                        transformer["metrics"]["attack_detection_rate"],
                    "mean_detection_delay_timesteps":
                        transformer["metrics"]["mean_detection_delay_timesteps"],
                    "false_positive_scenario_count":
                        transformer["metrics"]["false_positive_scenario_count"],
                },
                "reason": (
                    "No promotion: zero reported detection delay alone is not "
                    "sufficient to establish meaningful improvement. One false-"
                    "positive fault scenario is present and required holdout, "
                    "calibration, robustness, and runtime evidence is absent."
                ),
            },
            "graphsage": {
                "promotion": "REJECT",
                "reason": (
                    "No promotion: GraphSAGE evidence is from a controlled "
                    "structural benchmark, not a final holdout, and required "
                    "critical-service localization and IT-to-OT path plausibility "
                    "evidence is absent."
                ),
            },
            "gatv2": {
                "promotion": "REJECT",
                "reason": (
                    "No promotion: GATv2 evidence is from a controlled structural "
                    "benchmark, not a final holdout, and required critical-service "
                    "localization and IT-to-OT path plausibility evidence is absent."
                ),
            },
        },
        "graph_evidence_summary": {
            "benchmark_type": graph["benchmark_type"],
            "final_holdout_used": graph["final_holdout_used"],
            "energy_results_present": "energy" in graph["results"],
            "petrochemical_results_present": "petrochemical" in graph["results"],
        },
        "required_follow_up_evidence": [
            "Untouched final holdout evaluated once after thresholds are frozen.",
            "Separate energy and petrochemical scorecards.",
            "Direct comparison against the simpler baseline.",
            "Brier score, log loss, reliability diagram, and expected calibration error.",
            "p50/p95 latency, memory, cold/warm load, and timeout/error rate.",
            "Critical-service localization recall.",
            "IT-to-OT path plausibility for graph methods.",
            "Benign-operation false-positive families.",
        ],
        "stage_8_exit_statement": (
            "Every challenger has an explicit promotion/rejection rationale. "
            "No temporal or learned graph challenger is promoted from the current "
            "evidence. Deterministic weighted graph propagation remains the "
            "auditable graph baseline."
        ),
        "rw0806_matrix_status": matrix["status"],
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("RW-080-7: PASS")
    print("decision: NO_CHALLENGER_PROMOTED")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
