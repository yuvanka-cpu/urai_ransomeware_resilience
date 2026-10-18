"""Variant-independent deterministic seeds for Cycle 3 measurements.

This module does not generate events, labels, or model predictions.

Measurement seeds deliberately exclude scenario variant, scenario ID,
and development/calibration split.

A shared seed does not itself establish statistical independence,
realism, or freedom from label leakage.
"""

import hashlib


MEASUREMENT_SEED_NAMESPACE = "urai-cycle3-measurement-v1"


def build_cycle3_measurement_seed(
    *,
    base_seed: int,
    sector: str,
    asset_id: str,
    use_case_id: str,
) -> int:
    """Return a stable seed for one sector/asset/use-case combination."""

    if type(base_seed) is not int or base_seed < 0:
        raise ValueError("base_seed must be a nonnegative integer")

    for name, value in (
        ("sector", sector),
        ("asset_id", asset_id),
        ("use_case_id", use_case_id),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a nonempty string")

    # Length-prefixed encoding avoids ambiguous field boundaries.
    components = (
        MEASUREMENT_SEED_NAMESPACE,
        str(base_seed),
        sector,
        asset_id,
        use_case_id,
    )

    material = "".join(
        f"{len(component)}:{component}"
        for component in components
    )

    digest = hashlib.sha256(
        material.encode("utf-8")
    ).hexdigest()

    return int(digest[:16], 16)
