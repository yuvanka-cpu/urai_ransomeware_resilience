from __future__ import annotations

FORBIDDEN_DEPLOYED_FEATURES = frozenset(
    {
        "scenario_id",
        "scenario_seed",
        "is_ransomware",
        "incident_stage_truth",
        "affected_asset_truth",
        "blast_radius_truth",
        "analyst_disposition",
    }
)


def validate_deployed_features(feature_names: list[str]) -> None:
    """Reject ground-truth or future-information fields from deployed features."""
    normalized = {name.strip().lower() for name in feature_names}
    leakage = sorted(normalized & FORBIDDEN_DEPLOYED_FEATURES)

    if leakage:
        raise ValueError(
            "RW-050-5 feature leakage detected: " + ", ".join(leakage)
        )
