"""RW-140-1: Offline temporal detection evaluation audit.

Evaluates supplied prediction probabilities against an independently
supplied synthetic onset index.

Does not infer attack onset from scenario labels, stages, or model scores.
Does not establish operational detection performance.
"""

from math import isfinite


SCOPE = "offline_synthetic_temporal_evaluation"


def evaluate_temporal_detection(
    probabilities,
    onset_index,
    threshold=0.5,
):
    """Evaluate first alerts and post-onset detection timing."""

    def unavailable(reason):
        return {
            "status": "unavailable",
            "scope": SCOPE,
            "reason": reason,
        }

    if not isinstance(probabilities, (list, tuple)) or not probabilities:
        return unavailable("A nonempty probability sequence is required.")

    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        return unavailable("Detection threshold must be numeric.")

    if not isfinite(threshold) or not 0 < threshold <= 1:
        return unavailable("Detection threshold must be within (0, 1].")

    for probability in probabilities:
        if isinstance(probability, bool):
            return unavailable("Boolean probabilities are invalid.")

        if not isinstance(probability, (int, float)):
            return unavailable("Probabilities must be numeric.")

        if not isfinite(probability) or not 0 <= probability <= 1:
            return unavailable("Probabilities must be finite and within [0, 1].")

    if type(onset_index) is not int:
        return unavailable("An independently supplied onset index is required.")

    if not 0 <= onset_index < len(probabilities):
        return unavailable("Onset index is outside the observed sequence.")

    alert_indices = [
        index
        for index, probability in enumerate(probabilities)
        if probability >= threshold
    ]

    pre_onset_alerts = [
        index
        for index in alert_indices
        if index < onset_index
    ]

    post_onset_alerts = [
        index
        for index in alert_indices
        if index >= onset_index
    ]

    first_alert = alert_indices[0] if alert_indices else None
    first_post_onset = (
        post_onset_alerts[0] if post_onset_alerts else None
    )

    return {
        "status": "available",
        "scope": SCOPE,
        "threshold": float(threshold),
        "observation_count": len(probabilities),
        "onset_index": onset_index,
        "first_alert_index": first_alert,
        "pre_onset_alert_count": len(pre_onset_alerts),
        "pre_onset_alert_indices": pre_onset_alerts,
        "first_post_onset_alert_index": first_post_onset,
        "post_onset_detected": first_post_onset is not None,
        "post_onset_detection_delay_timesteps": (
            first_post_onset - onset_index
            if first_post_onset is not None
            else None
        ),
        "limitations": (
            "Synthetic offline evaluation only. Onset must be supplied "
            "independently. Pre-onset alerts are not proof of advance "
            "warning. Detection delay is measured in timesteps, not "
            "operational minutes or MTTD."
        ),
    }
