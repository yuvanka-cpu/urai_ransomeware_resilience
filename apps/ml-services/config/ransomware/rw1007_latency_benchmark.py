"""RW-100-7 exact-runtime warm latency benchmark."""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from fastapi.testclient import TestClient

from config.ransomware.rw1006_internal_api import app


@dataclass(frozen=True)
class BenchmarkResult:
    runs: int
    warmup_runs: int
    p50_ms: float
    p95_ms: float
    max_ms: float
    p95_under_one_second: bool


PAYLOAD = {
    "schema_version": "1.0",
    "mode": "synthetic_scenario",
    "industry": "energy",
    "site_id": "demo-site",
    "site_type": "substation",
    "scenario_id": "rw-attack-070891bdbaec",
    "observable_input": {},
}


def benchmark(*, runs: int = 50, warmup_runs: int = 10) -> BenchmarkResult:
    client = TestClient(app)

    for _ in range(warmup_runs):
        response = client.post("/internal/ransomware/infer", json=PAYLOAD)
        response.raise_for_status()

    timings_ms: list[float] = []

    for _ in range(runs):
        started = time.perf_counter()
        response = client.post("/internal/ransomware/infer", json=PAYLOAD)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.raise_for_status()
        timings_ms.append(elapsed_ms)

    timings_ms.sort()
    p95_index = max(0, int(runs * 0.95) - 1)

    return BenchmarkResult(
        runs=runs,
        warmup_runs=warmup_runs,
        p50_ms=statistics.median(timings_ms),
        p95_ms=timings_ms[p95_index],
        max_ms=max(timings_ms),
        p95_under_one_second=timings_ms[p95_index] < 1000,
    )


if __name__ == "__main__":
    result = benchmark()

    report = {
        "task_id": "RW-100-7",
        "benchmark": "exact_runtime_warm",
        "endpoint": "/internal/ransomware/infer",
        "result": asdict(result),
        "gate": {
            "requirement": "warm p95 below one second",
            "passed": result.p95_under_one_second,
        },
    }

    output = Path("artifacts/ransomware/offline/rw1007_latency_report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("=== RW-100-7 LATENCY BENCHMARK ===")
    print(f"Runs: {result.runs}")
    print(f"Warmup runs: {result.warmup_runs}")
    print(f"P50: {result.p50_ms:.3f} ms")
    print(f"P95: {result.p95_ms:.3f} ms")
    print(f"Max: {result.max_ms:.3f} ms")
    print(f"P95 < 1 second: {result.p95_under_one_second}")
    print(f"Report: {output}")
