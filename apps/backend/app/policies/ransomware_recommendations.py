from typing import Any


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
        recommendations.append(
            "Do not infer a live-model result; review the dependency failure."
        )

    if evidence:
        recommendations.append(
            "Trace each recommendation to the corresponding scored evidence."
        )

    return recommendations
