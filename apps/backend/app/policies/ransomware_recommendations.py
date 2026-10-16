"""Advisory, evidence-aware recommendations for synthetic ransomware analysis.

Component scores are model signals, not causal forensic evidence.
No operational actions are executed or authorized here.
"""

import math


SIGNAL_GUIDANCE = {
    "rule_score": (
        "Review the rule-based detection signal alongside the available "
        "synthetic event evidence."
    ),
    "anomaly_score": (
        "Examine the observable behaviour associated with the anomaly signal; "
        "the score alone does not identify a cause."
    ),
    "graph_score": (
        "Review available relationship and dependency evidence; the graph "
        "score does not establish a propagation path."
    ),
    "catboost_score": (
        "Compare the CatBoost classifier signal with other detection signals "
        "and available event records."
    ),
}


def assemble_recommendations(
    *,
    decision: str,
    evidence: list[str],
) -> list[str]:
    recommendations: list[str] = []

    if decision == "normal":
        recommendations.append(
            "Continue monitoring the available synthetic evidence."
        )
    elif decision == "investigate":
        recommendations.append(
            "Review the scored evidence and investigate the suspected activity."
        )
    elif decision == "high_risk":
        recommendations.append(
            "Escalate the scored evidence for human review."
        )
    elif decision == "unavailable":
        return [
            "Do not infer a live-model result; review the dependency failure."
        ]
    else:
        return ["Decision unavailable; request human review of the result."]

    if not isinstance(evidence, list):
        return recommendations

    valid_signals = set()

    for item in evidence:
        if not isinstance(item, str) or "=" not in item:
            continue

        name, raw_value = item.split("=", 1)
        name = name.strip()

        if name not in SIGNAL_GUIDANCE:
            continue

        try:
            value = float(raw_value.strip())
        except (TypeError, ValueError):
            continue

        if math.isfinite(value) and 0 <= value <= 1:
            valid_signals.add(name)

    if valid_signals:
        recommendations.append(
            "Trace each recommendation to the corresponding scored evidence."
        )
        for name in SIGNAL_GUIDANCE:
            if name in valid_signals:
                recommendations.append(SIGNAL_GUIDANCE[name])
    elif evidence:
        recommendations.append(
            "Supporting model signals are unavailable or unverified; "
            "review the source evidence before drawing conclusions."
        )

    return recommendations
