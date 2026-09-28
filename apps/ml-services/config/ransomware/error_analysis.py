from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from catboost import CatBoostClassifier

from config.ransomware.catboost_trainer import (
    build_rows,
    load_and_verify_scenarios,
)
from config.ransomware.features.window_features import (
    extract_window_features,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
)


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    ROOT / "artifacts/ransomware/models/rw0704_catboost_model.cbm"
)
TRAINING_MANIFEST_PATH = (
    ROOT
    / "artifacts/ransomware/models/rw0704_catboost_training_manifest.json"
)
REPORT_PATH = (
    ROOT
    / "artifacts/ransomware/offline/rw0708_error_analysis.json"
)

WINDOWS = (1, 5, 15)
THRESHOLD = 0.5
SEED = 20260921
EXPECTED_FEATURE_COUNT = 54
MAX_EXAMPLES_PER_FAMILY = 3

BENIGN_FAMILIES = (
    "patching",
    "deployment",
    "bulk_copy",
    "compression",
    "backup",
    "restore_test",
    "approved_administration",
    "vendor_support",
    "relay_configuration_work",
    "turnaround_work",
    "failover",
    "historian_replay",
    "campaign_changes",
)

FAULT_FAMILIES = (
    "host_outage",
    "network_interruption",
    "disk_pressure",
    "backup_failure",
    "source_loss",
    "reordered_late_events",
    "partial_evidence",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def parse_event_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value

    return datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    )


def load_training_manifest() -> dict[str, Any]:
    return json.loads(
        TRAINING_MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )


def build_model_matrix(
    model: CatBoostClassifier,
    feature_names: list[str],
    scenario: Any,
    end_time: datetime,
) -> list[list[Any]]:
    events = assemble_scenario_events(scenario)

    matrix: list[list[Any]] = []

    for window_minutes in WINDOWS:
        features = extract_window_features(
            events,
            end_time=end_time,
            duration_minutes=window_minutes,
        )

        if sorted(features) != feature_names:
            raise ValueError(
                "Observable feature contract mismatch"
            )

        matrix.append(
            [
                features[name]
                for name in feature_names
            ]
            + [
                scenario.industry,
                "|".join(sorted(scenario.site_types)),
            ]
        )

    if model.feature_names_ is None:
        raise ValueError("Saved model has no feature names")

    if len(model.feature_names_) != (
        len(feature_names) + 2
    ):
        raise ValueError(
            "Saved model width does not match "
            "54 observable + 2 categorical context fields"
        )

    return matrix


def window_events(
    events: list[Any],
    end_time: datetime,
    duration_minutes: int,
) -> list[Any]:
    start_time = (
        end_time
        - timedelta(minutes=duration_minutes)
    )

    selected = []

    for event in events:
        event_time = parse_event_time(event.event_time)

        if start_time <= event_time <= end_time:
            selected.append(event)

    return sorted(
        selected,
        key=lambda event: (
            parse_event_time(event.event_time),
            event.event_family,
            event.event_type,
        ),
    )


def serialize_event(event: Any) -> dict[str, Any]:
    return {
        "event_time": parse_event_time(
            event.event_time
        ).isoformat(),
        "event_family": event.event_family,
        "event_type": event.event_type,
        "asset_id": event.asset_id,
        "attributes": dict(event.attributes),
    }


def build_trace(
    scenario: Any,
    events: list[Any],
    anchor_event: Any,
    window_minutes: int,
    probability: float,
) -> dict[str, Any]:
    end_time = parse_event_time(
        anchor_event.event_time
    )

    trace_events = window_events(
        events,
        end_time,
        window_minutes,
    )

    return {
        "scenario_id": scenario.scenario_id,
        "industry": scenario.industry,
        "site_types": sorted(scenario.site_types),
        "asset_id": scenario.asset_id,
        "window_minutes": window_minutes,
        "anchor_event": {
            "event_time": end_time.isoformat(),
            "event_family": anchor_event.event_family,
            "event_type": anchor_event.event_type,
            "asset_id": anchor_event.asset_id,
            "attributes": dict(anchor_event.attributes),
        },
        "probability": probability,
        "threshold": THRESHOLD,
        "predicted_attack": int(
            probability >= THRESHOLD
        ),
        "events_in_window": [
            serialize_event(event)
            for event in trace_events
        ],
    }


def evaluate_family(
    model: CatBoostClassifier,
    scenario_list: list[Any],
    family_names: tuple[str, ...],
    feature_names: list[str],
    variant_name: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for family_name in family_names:
        all_probabilities: list[float] = []
        false_positive_examples: list[
            dict[str, Any]
        ] = []

        for scenario in scenario_list:
            events = assemble_scenario_events(
                scenario
            )

            anchors = [
                event
                for event in events
                if event.event_type == family_name
            ]

            if len(anchors) != 1:
                raise ValueError(
                    f"Expected exactly one {family_name} "
                    f"anchor in {scenario.scenario_id}; "
                    f"found {len(anchors)}"
                )

            anchor = anchors[0]
            end_time = parse_event_time(
                anchor.event_time
            )

            matrix = build_model_matrix(
                model,
                feature_names,
                scenario,
                end_time,
            )

            probabilities = model.predict_proba(
                matrix
            )[:, 1].tolist()

            for window_minutes, probability in zip(
                WINDOWS,
                probabilities,
                strict=True,
            ):
                probability = float(probability)
                all_probabilities.append(probability)

                if probability >= THRESHOLD:
                    false_positive_examples.append(
                        build_trace(
                            scenario,
                            events,
                            anchor,
                            window_minutes,
                            probability,
                        )
                    )

        false_positive_examples.sort(
            key=lambda item: item["probability"],
            reverse=True,
        )

        false_positive_count = len(
            false_positive_examples
        )
        total_windows = len(all_probabilities)

        result[family_name] = {
            "variant": variant_name,
            "scenarios": len(scenario_list),
            "windows_per_scenario": len(WINDOWS),
            "total_windows": total_windows,
            "false_positive_count": (
                false_positive_count
            ),
            "false_positive_rate": (
                false_positive_count / total_windows
                if total_windows
                else None
            ),
            "threshold": THRESHOLD,
            "max_probability": (
                max(all_probabilities)
                if all_probabilities
                else None
            ),
            "mean_probability": (
                sum(all_probabilities)
                / len(all_probabilities)
                if all_probabilities
                else None
            ),
            "example_traces": false_positive_examples[
                :MAX_EXAMPLES_PER_FAMILY
            ],
            "trace_semantics": (
                "The family event is the window anchor. "
                "A 5-minute or 15-minute window may also "
                "contain nearby observable events from the "
                "same synthetic scenario."
            ),
        }

    return result


def build_attack_false_negative_examples(
    model: CatBoostClassifier,
    attack_scenarios: list[Any],
    feature_names: list[str],
) -> dict[str, Any]:
    examples: list[dict[str, Any]] = []
    total_windows = 0
    false_negative_count = 0

    for scenario in attack_scenarios:
        events = assemble_scenario_events(
            scenario
        )

        anchor = events[-1]
        end_time = parse_event_time(
            anchor.event_time
        )

        matrix = build_model_matrix(
            model,
            feature_names,
            scenario,
            end_time,
        )

        probabilities = model.predict_proba(
            matrix
        )[:, 1].tolist()

        for window_minutes, probability in zip(
            WINDOWS,
            probabilities,
            strict=True,
        ):
            probability = float(probability)
            total_windows += 1

            if probability < THRESHOLD:
                false_negative_count += 1

                examples.append(
                    build_trace(
                        scenario,
                        events,
                        anchor,
                        window_minutes,
                        probability,
                    )
                )

    examples.sort(
        key=lambda item: item["probability"]
    )

    return {
        "attack_scenarios": len(
            attack_scenarios
        ),
        "total_windows": total_windows,
        "false_negative_count": false_negative_count,
        "false_negative_rate": (
            false_negative_count / total_windows
            if total_windows
            else None
        ),
        "threshold": THRESHOLD,
        "example_traces": examples[
            :MAX_EXAMPLES_PER_FAMILY
        ],
    }


def main() -> None:
    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    training_manifest = (
        load_training_manifest()
    )

    if training_manifest["base_seed"] != SEED:
        raise ValueError(
            "Training manifest seed mismatch"
        )

    feature_names = list(
        training_manifest[
            "observable_feature_names"
        ]
    )

    if len(feature_names) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} "
            f"observable features, found "
            f"{len(feature_names)}"
        )

    model = CatBoostClassifier()
    model.load_model(str(MODEL_PATH))

    if model.feature_names_ is None:
        raise ValueError(
            "Saved CatBoost model has no feature names"
        )

    expected_model_width = (
        len(feature_names) + 2
    )

    if len(model.feature_names_) != (
        expected_model_width
    ):
        raise ValueError(
            "Saved CatBoost model width mismatch"
        )

    _, frozen = load_and_verify_scenarios()

    rows, regenerated_feature_names = build_rows(
        frozen
    )

    if regenerated_feature_names != feature_names:
        raise ValueError(
            "Regenerated feature contract differs "
            "from RW-070-4 manifest"
        )

    test_scenarios = [
        scenario
        for scenario in frozen
        if scenario.split == "test"
    ]

    benign_scenarios = [
        scenario
        for scenario in test_scenarios
        if scenario.variant == "benign"
    ]

    fault_scenarios = [
        scenario
        for scenario in test_scenarios
        if scenario.variant == "fault"
    ]

    attack_scenarios = [
        scenario
        for scenario in test_scenarios
        if scenario.variant == "attack"
    ]

    if len(test_scenarios) != 14:
        raise ValueError(
            f"Expected 14 test scenarios, found "
            f"{len(test_scenarios)}"
        )

    if len(benign_scenarios) != 4:
        raise ValueError(
            f"Expected 4 benign test scenarios, found "
            f"{len(benign_scenarios)}"
        )

    if len(fault_scenarios) != 2:
        raise ValueError(
            f"Expected 2 fault test scenarios, found "
            f"{len(fault_scenarios)}"
        )

    if len(attack_scenarios) != 6:
        raise ValueError(
            f"Expected 6 attack test scenarios, found "
            f"{len(attack_scenarios)}"
        )

    report = {
        "evidence_id": "RW-070-8",
        "artifact_type": "benign_failure_error_analysis",
        "report_version": "1.0",
        "base_seed": SEED,
        "evaluated_split": "test",
        "sealed_split": {
            "name": "untouched_holdout",
            "status": "sealed_not_evaluated",
        },
        "model": {
            "path": str(
                MODEL_PATH.relative_to(ROOT)
            ),
            "sha256": sha256_file(MODEL_PATH),
            "observable_feature_count": len(
                feature_names
            ),
            "categorical_context_features": [
                "industry",
                "site_types",
            ],
            "threshold": THRESHOLD,
        },
        "population": {
            "test_scenarios": len(test_scenarios),
            "benign_scenarios": len(
                benign_scenarios
            ),
            "fault_scenarios": len(
                fault_scenarios
            ),
            "attack_scenarios": len(
                attack_scenarios
            ),
            "windows_minutes": list(WINDOWS),
        },
        "benign_family_analysis": evaluate_family(
            model,
            benign_scenarios,
            BENIGN_FAMILIES,
            feature_names,
            "benign",
        ),
        "failure_family_analysis": evaluate_family(
            model,
            fault_scenarios,
            FAULT_FAMILIES,
            feature_names,
            "fault",
        ),
        "attack_false_negative_analysis": (
            build_attack_false_negative_examples(
                model,
                attack_scenarios,
                feature_names,
            )
        ),
        "interpretation": {
            "benign_family_definition": (
                "False positive measured on windows anchored "
                "to the named benign-family observable event."
            ),
            "failure_family_definition": (
                "False positive measured on windows anchored "
                "to the named telemetry/failure observable event."
            ),
            "truth_boundary": (
                "Scenario variant and hidden truth are used "
                "only to select evaluation populations and "
                "label the error-analysis report; they are "
                "not supplied as model features."
            ),
            "observable_trace_boundary": (
                "Example traces contain only assembled observable "
                "event family, event type, asset identifier, "
                "timestamp and event attributes."
            ),
            "holdout_boundary": (
                "No untouched-holdout scenario is loaded for "
                "scoring or example selection."
            ),
        },
        "requested_error_classes": [
            "patching",
            "deployment",
            "backup",
            "compression",
            "approved_administration",
            "restore_test",
            "vendor_support",
            "failures",
        ],
    }

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print("RW-070-8: PASS")
    print("test_scenarios:", len(test_scenarios))
    print("benign_scenarios:", len(benign_scenarios))
    print("fault_scenarios:", len(fault_scenarios))
    print("attack_scenarios:", len(attack_scenarios))
    print("benign_families:", len(BENIGN_FAMILIES))
    print("failure_families:", len(FAULT_FAMILIES))
    print("threshold:", THRESHOLD)
    print("report:", REPORT_PATH)


if __name__ == "__main__":
    main()
