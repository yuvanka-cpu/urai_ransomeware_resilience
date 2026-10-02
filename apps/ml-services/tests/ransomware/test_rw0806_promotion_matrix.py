import json
from pathlib import Path


ARTIFACT = Path("artifacts/ransomware/offline/rw0806_promotion_matrix.json")


def test_rw0806_promotion_matrix_is_conservative_and_complete():
    assert ARTIFACT.exists()

    report = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    assert report["task"] == "RW-080-6"
    assert report["status"] == "PASS"
    assert report["synthetic_only"] is True
    assert report["real_action_executed"] is False

    expected = {
        "tabpfn_v3_5",
        "tcn",
        "compact_transformer",
        "graphsage",
        "gatv2",
    }

    assert set(report["challengers"]) == expected
    assert all(
        report["challengers"][name]["promotion"] == "REJECT"
        for name in expected
    )

    assert report["retained_baseline"]["graph_method"] == (
        "deterministic_weighted_graph_propagation"
    )
