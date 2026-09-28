import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = (
    ROOT
    / "artifacts/ransomware/offline/rw0705_shap_provenance_report.json"
)
PROVENANCE = (
    ROOT
    / "artifacts/ransomware/offline/rw0705_feature_provenance.json"
)


def test_shap_report_passed():
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert report["evidence_id"] == "RW-070-5"
    assert report["status"] == "pass"
    assert report["observable_feature_count"] == 54
    assert report["model_input_feature_count"] == 56
    assert report["provenance_test"] is True
    assert report["repeated_shap_deterministic"] is True


def test_shap_matrix_has_bias_column():
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    rows, columns = report["shap_matrix_shape"]

    assert rows == report["samples_generated"]
    assert columns == report["model_input_feature_count"] + 1


def test_displayed_features_are_observable():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    provenance = json.loads(
        PROVENANCE.read_text(encoding="utf-8")
    )

    allowed = set(
        provenance["observable_feature_names"]
    )

    for sample in report["sample_explanations"]:
        for item in sample["displayed_observable_features"]:
            feature = item["feature"]

            assert feature in allowed
            assert (
                provenance["features"][feature]["source_kind"]
                == "observable_event"
            )
            assert provenance["features"][feature]["display_allowed"] is True
            assert (
                provenance["features"][feature]["truth_or_future_field"]
                is False
            )


def test_context_features_are_not_displayed():
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    context = set(
        report["context_features_excluded_from_display"]
    )

    for sample in report["sample_explanations"]:
        for item in sample["displayed_observable_features"]:
            assert item["feature"] not in context
