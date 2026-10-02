import json
from pathlib import Path


REPORT = Path("artifacts/ransomware/offline/rw1007_latency_report.json")


def test_rw1007_latency_report_exists_and_passes():
    assert REPORT.exists()

    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert report["task_id"] == "RW-100-7"
    assert report["benchmark"] == "exact_runtime_warm"
    assert report["result"]["runs"] == 50
    assert report["result"]["warmup_runs"] == 10
    assert report["result"]["p95_ms"] < 1000
    assert report["result"]["p95_under_one_second"] is True
    assert report["gate"]["passed"] is True
