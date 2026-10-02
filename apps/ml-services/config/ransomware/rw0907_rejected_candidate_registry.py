"""RW-090-7 rejected-candidate registry.

Synthetic ransomware-resilience PoC only.

Records every challenger that was evaluated but not promoted,
using the authoritative RW-080-6/RW-080-7 promotion evidence.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OFFLINE_DIR = ROOT / "artifacts" / "ransomware" / "offline"

SOURCE_MATRIX = OFFLINE_DIR / "rw0806_promotion_matrix.json"
SOURCE_DECISION = OFFLINE_DIR / "rw0807_promotion_decision.json"

OUTPUT = OFFLINE_DIR / "rw0907_rejected_candidate_registry.json"

EXPECTED_REJECTIONS = {
    "tcn",
    "compact_transformer",
    "graphsage",
    "gatv2",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_registry() -> dict[str, Any]:
    matrix = load_json(SOURCE_MATRIX)
    decision = load_json(SOURCE_DECISION)

    if decision.get("decision") != "NO_CHALLENGER_PROMOTED":
        raise ValueError(
            "RW-080-7 does not state NO_CHALLENGER_PROMOTED."
        )

    decisions = decision.get("decisions", {})

    actual_rejections = {
        name
        for name, record in decisions.items()
        if record.get("promotion") == "REJECT"
    }

    if actual_rejections != EXPECTED_REJECTIONS:
        raise ValueError(
            "Unexpected rejected-candidate set: "
            f"{sorted(actual_rejections)}"
        )

    candidates = []

    for name in sorted(EXPECTED_REJECTIONS):
        record = decisions[name]

        candidates.append(
            {
                "candidate": name,
                "promotion_status": record["promotion"],
                "reason": record["reason"],
                "evidence": record.get("evidence", {}),
                "source_task": "RW-080-7",
            }
        )

    return {
        "task": "RW-090-7",
        "artifact_type": "rejected_candidate_registry",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "synthetic_only": True,

        "promotion_boundary": {
            "final_decision": "NO_CHALLENGER_PROMOTED",
            "rejected_candidate_count": len(candidates),
            "all_rejected_candidates_recorded": True,
        },

        "candidates": candidates,

        "retained_auditable_baseline": {
            "component": "deterministic_weighted_graph_propagation",
            "status": "retained_baseline",
            "reason": (
                "Retained as an auditable graph baseline; "
                "not treated as a promoted novel challenger."
            ),
        },

        "source_artifacts": [
            "artifacts/ransomware/offline/rw0806_promotion_matrix.json",
            "artifacts/ransomware/offline/rw0807_promotion_decision.json",
        ],

        "contract": {
            "promotion_by_novelty_forbidden": True,
            "promotion_by_pool_accuracy_forbidden": True,
            "final_holdout_used": False,
            "calibration_evidence_required": True,
            "runtime_evidence_required": True,
            "human_approval_required": True,
            "real_action_executed": False,
            "operational_state_claimed": False,
        },
    }


def main() -> None:
    registry = build_registry()

    OUTPUT.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("=== RW-090-7 COMPLETE ===")
    print(f"Registry: {OUTPUT}")
    print(
        "Rejected candidates:",
        registry["promotion_boundary"]["rejected_candidate_count"],
    )
    print(
        "Final decision:",
        registry["promotion_boundary"]["final_decision"],
    )


if __name__ == "__main__":
    main()
