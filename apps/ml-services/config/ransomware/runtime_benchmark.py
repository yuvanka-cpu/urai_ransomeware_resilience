from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import ctypes
from ctypes import wintypes

from catboost import CatBoostClassifier

from config.ransomware.catboost_trainer import (
    build_rows,
    load_and_verify_scenarios,
)
from config.ransomware.evaluation_scorecard import model_matrix


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    ROOT / "artifacts/ransomware/models/rw0704_catboost_model.cbm"
)
TRAINING_MANIFEST_PATH = (
    ROOT
    / "artifacts/ransomware/models/rw0704_catboost_training_manifest.json"
)
REPORT_PATH = (
    ROOT / "artifacts/ransomware/offline/rw0707_runtime_benchmark.json"
)

WINDOWS = (1, 5, 15)
SEED = 20260921
WARM_LOAD_RUNS = 10
COLD_LOAD_RUNS = 5
INFERENCE_WARMUP_RUNS = 10
INFERENCE_TIMED_RUNS = 50


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def process_memory_bytes() -> int:
    psapi = ctypes.WinDLL("Psapi.dll")
    kernel32 = ctypes.WinDLL("Kernel32.dll")

    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE

    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)

    process = kernel32.GetCurrentProcess()

    ok = psapi.GetProcessMemoryInfo(
        process,
        ctypes.byref(counters),
        wintypes.DWORD(ctypes.sizeof(counters)),
    )

    if not ok:
        error_code = ctypes.get_last_error()
        raise OSError(
            error_code,
            "GetProcessMemoryInfo failed",
        )

    return int(counters.WorkingSetSize)


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def timed_load() -> tuple[CatBoostClassifier, float, int]:
    started = time.perf_counter_ns()

    model = CatBoostClassifier()
    model.load_model(str(MODEL_PATH))

    elapsed_ms = (
        time.perf_counter_ns() - started
    ) / 1_000_000.0

    memory = process_memory_bytes()

    return model, elapsed_ms, memory


def cold_child() -> None:
    _, elapsed_ms, memory = timed_load()

    print(
        json.dumps(
            {
                "load_ms": elapsed_ms,
                "working_set_bytes": memory,
            }
        )
    )


def percentile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("Cannot calculate percentile of empty list")

    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower

    return (
        ordered[lower]
        + (ordered[upper] - ordered[lower]) * fraction
    )


def main() -> None:
    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    training_manifest = json.loads(
        TRAINING_MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )

    if training_manifest["base_seed"] != SEED:
        raise ValueError("Training manifest seed mismatch")

    feature_names = list(
        training_manifest["observable_feature_names"]
    )

    if len(feature_names) != 54:
        raise ValueError(
            f"Expected 54 observable features, found {len(feature_names)}"
        )

    _, frozen = load_and_verify_scenarios()
    rows, regenerated_feature_names = build_rows(frozen)

    if regenerated_feature_names != feature_names:
        raise ValueError(
            "Runtime benchmark feature contract mismatch"
        )

    test_rows = [
        row
        for row in rows
        if row.split == "test"
    ]

    if len(test_rows) != 42:
        raise ValueError(
            f"Expected 42 test rows, found {len(test_rows)}"
        )

    matrix = model_matrix(
        test_rows,
        feature_names,
    )

    cold_load_ms: list[float] = []
    cold_memory_bytes: list[int] = []

    for _ in range(COLD_LOAD_RUNS):
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--cold-child",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        child_payload = json.loads(
            completed.stdout.strip()
        )
        cold_load_ms.append(
            float(child_payload["load_ms"])
        )
        cold_memory_bytes.append(
            int(child_payload["working_set_bytes"])
        )

    model = CatBoostClassifier()

    warm_load_ms: list[float] = []
    warm_memory_bytes: list[int] = []

    for _ in range(WARM_LOAD_RUNS):
        started = time.perf_counter_ns()

        warm_model = CatBoostClassifier()
        warm_model.load_model(str(MODEL_PATH))

        elapsed_ms = (
            time.perf_counter_ns() - started
        ) / 1_000_000.0

        warm_load_ms.append(elapsed_ms)
        warm_memory_bytes.append(
            process_memory_bytes()
        )

        del warm_model

    model, _, _ = timed_load()

    for _ in range(INFERENCE_WARMUP_RUNS):
        model.predict_proba(matrix)

    inference_ms: list[float] = []

    for _ in range(INFERENCE_TIMED_RUNS):
        started = time.perf_counter_ns()
        model.predict_proba(matrix)
        elapsed_ms = (
            time.perf_counter_ns() - started
        ) / 1_000_000.0

        inference_ms.append(elapsed_ms)

    peak_memory_bytes = max(
        cold_memory_bytes
        + warm_memory_bytes
        + [process_memory_bytes()]
    )

    report: dict[str, Any] = {
        "evidence_id": "RW-070-7",
        "artifact_type": "runtime_benchmark",
        "report_version": "1.0",
        "base_seed": SEED,
        "runtime": {
            "python": sys.version,
            "platform": sys.platform,
            "catboost_version": "1.2.10",
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
            "model_input_feature_count": len(
                feature_names
            ) + 2,
        },
        "benchmark_population": {
            "evaluated_split": "test",
            "test_rows": len(test_rows),
            "windows_minutes": list(WINDOWS),
            "inference_batch_size": len(matrix),
        },
        "cold_load": {
            "runs": COLD_LOAD_RUNS,
            "latency_ms": {
                "p50": percentile(cold_load_ms, 0.50),
                "p95": percentile(cold_load_ms, 0.95),
                "min": min(cold_load_ms),
                "max": max(cold_load_ms),
                "mean": statistics.mean(cold_load_ms),
            },
            "working_set_mb": {
                "max": max(cold_memory_bytes) / (
                    1024 * 1024
                ),
                "mean": statistics.mean(
                    cold_memory_bytes
                ) / (1024 * 1024),
            },
        },
        "warm_load": {
            "runs": WARM_LOAD_RUNS,
            "latency_ms": {
                "p50": percentile(warm_load_ms, 0.50),
                "p95": percentile(warm_load_ms, 0.95),
                "min": min(warm_load_ms),
                "max": max(warm_load_ms),
                "mean": statistics.mean(warm_load_ms),
            },
            "working_set_mb": {
                "max": max(warm_memory_bytes) / (
                    1024 * 1024
                ),
                "mean": statistics.mean(
                    warm_memory_bytes
                ) / (1024 * 1024),
            },
        },
        "warm_inference": {
            "warmup_runs": INFERENCE_WARMUP_RUNS,
            "timed_runs": INFERENCE_TIMED_RUNS,
            "batch_size": len(matrix),
            "latency_ms": {
                "p50": percentile(inference_ms, 0.50),
                "p95": percentile(inference_ms, 0.95),
                "min": min(inference_ms),
                "max": max(inference_ms),
                "mean": statistics.mean(inference_ms),
            },
        },
        "memory": {
            "peak_working_set_mb": (
                peak_memory_bytes
                / (1024 * 1024)
            ),
            "measurement": (
                "Windows GetProcessMemoryInfo WorkingSetSize"
            ),
        },
        "holdout_policy": {
            "untouched_holdout_loaded": False,
            "untouched_holdout_evaluated": False,
        },
        "notes": [
            "Cold-load measurements run in fresh child Python processes.",
            "Warm-load measurements repeat artifact loading in the same parent process after the cold benchmark.",
            "Warm inference measures predict_proba over the full frozen test batch after warm-up.",
            "Benchmark measures the committed CatBoost artifact only; it does not represent the later end-to-end API runtime gate.",
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

    print("RW-070-7: PASS")
    print("cold_load_p50_ms:", report["cold_load"]["latency_ms"]["p50"])
    print("cold_load_p95_ms:", report["cold_load"]["latency_ms"]["p95"])
    print("warm_load_p50_ms:", report["warm_load"]["latency_ms"]["p50"])
    print("warm_load_p95_ms:", report["warm_load"]["latency_ms"]["p95"])
    print("warm_inference_p50_ms:", report["warm_inference"]["latency_ms"]["p50"])
    print("warm_inference_p95_ms:", report["warm_inference"]["latency_ms"]["p95"])
    print("peak_working_set_mb:", report["memory"]["peak_working_set_mb"])
    print("report:", REPORT_PATH)


if __name__ == "__main__":
    if "--cold-child" in sys.argv:
        cold_child()
    else:
        main()
