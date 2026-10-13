"""RW-130-1: Offline data drift monitoring for the frozen feature contract."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from config.ransomware.rw1002_feature_contract import (
    EXPECTED_FEATURES,
    validate_feature_row,
)

MIN_SAMPLES = 30
PSI_THRESHOLD = 0.2
EPSILON = 1e-6


def population_stability_index(
    reference: Sequence[float],
    current: Sequence[float],
    bins: int = 10,
) -> float:
    """Calculate PSI using bins defined exclusively by reference data."""
    ref = np.asarray(reference, dtype=float)
    cur = np.asarray(current, dtype=float)

    if (
        ref.ndim != 1
        or cur.ndim != 1
        or len(ref) < MIN_SAMPLES
        or len(cur) < MIN_SAMPLES
        or not np.all(np.isfinite(ref))
        or not np.all(np.isfinite(cur))
        or bins < 2
    ):
        raise ValueError("Insufficient or invalid distribution data")

    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))

    if len(edges) == 1:
        reference_value = float(edges[0])

        if np.all(cur == reference_value):
            return 0.0

        # Two categories: unchanged reference value vs changed value.
        # Apply the same smoothing convention as histogram PSI.
        ref_counts = np.array([len(ref), 0], dtype=float)
        cur_counts = np.array(
            [
                np.count_nonzero(cur == reference_value),
                np.count_nonzero(cur != reference_value),
            ],
            dtype=float,
        )

        ref_pct = (ref_counts + EPSILON) / (
            len(ref) + EPSILON * len(ref_counts)
        )
        cur_pct = (cur_counts + EPSILON) / (
            len(cur) + EPSILON * len(cur_counts)
        )

        return float(
            np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        )

    edges[0] = -np.inf
    edges[-1] = np.inf

    ref_counts = np.histogram(ref, bins=edges)[0]
    cur_counts = np.histogram(cur, bins=edges)[0]

    ref_pct = (ref_counts + EPSILON) / (
        len(ref) + EPSILON * len(ref_counts)
    )
    cur_pct = (cur_counts + EPSILON) / (
        len(cur) + EPSILON * len(cur_counts)
    )

    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def monitor_data_drift(
    reference_rows: Sequence[Mapping[str, Any]] | None,
    current_rows: Sequence[Mapping[str, Any]] | None,
    *,
    threshold: float = PSI_THRESHOLD,
) -> dict[str, Any]:
    """Compare validated feature distributions without modifying inputs."""
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("threshold must be positive and finite")

    if (
        reference_rows is None
        or current_rows is None
        or len(reference_rows) < MIN_SAMPLES
        or len(current_rows) < MIN_SAMPLES
    ):
        return {
            "status": "unavailable",
            "reason": "Insufficient reference or current observations",
            "feature_psi": {},
        }

    try:
        for row in (*reference_rows, *current_rows):
            validate_feature_row(row)

        feature_psi = {}

        for feature in sorted(EXPECTED_FEATURES):
            reference = [row[feature] for row in reference_rows]
            current = [row[feature] for row in current_rows]

            feature_psi[feature] = population_stability_index(
                reference, current
            )

    except (ValueError, TypeError, KeyError) as exc:
        return {
            "status": "unavailable",
            "reason": str(exc),
            "feature_psi": {},
        }

    drifted = sorted(
        feature for feature, psi in feature_psi.items()
        if psi >= threshold
    )

    return {
        "status": (
            "drift_detected" if drifted else "no_drift_detected"
        ),
        "threshold": threshold,
        "reference_count": len(reference_rows),
        "current_count": len(current_rows),
        "feature_psi": feature_psi,
        "drifted_features": drifted,
    }
