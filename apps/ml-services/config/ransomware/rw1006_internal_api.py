from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from config.ransomware.baselines import RobustAnomalyBaseline
from config.ransomware.catboost_trainer import (
    build_rows,
    load_and_verify_scenarios,
)
from config.ransomware.graph_propagation import load_sector_graph
from config.ransomware.rw0901_oof_scores import (
    _anomaly_score,
    _graph_score,
    _rule_score,
)
from config.ransomware.rw1003_canonical_inference import canonical_inference
from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
)

API_SCHEMA_VERSION = "1.0"
TASK_ID = "RW-100-6"
MODE = "synthetic_scenario"
DEVELOPMENT_SPLITS = {"train", "validation"}

RESERVED_TRUTH_KEYS = {
    "ground_truth",
    "ground_truth_label",
    "synthetic_truth",
    "truth_label",
    "is_ransomware",
    "incident_stage_truth",
    "affected_asset_truth",
    "blast_radius_truth",
    "analyst_disposition",
}


class InternalInferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    mode: Literal["synthetic_scenario"]
    industry: Literal["energy", "petrochemical"]
    site_id: str = Field(min_length=1)
    site_type: Literal[
        "control_centre",
        "substation",
        "refinery",
        "petrochemical_complex",
    ]
    scenario_id: str = Field(min_length=1)
    observable_input: dict[str, Any] = Field(default_factory=dict)

    @field_validator("site_id", "scenario_id")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("observable_input")
    @classmethod
    def reject_truth_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        def walk(item: Any, path: str) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    normalized = str(key).strip().lower()
                    if normalized in RESERVED_TRUTH_KEYS:
                        raise ValueError(
                            f"ground-truth field is forbidden: {path}.{key}"
                        )
                    walk(child, f"{path}.{key}")
            elif isinstance(item, list):
                for index, child in enumerate(item):
                    walk(child, f"{path}[{index}]")

        walk(value, "observable_input")
        return value

    @model_validator(mode="after")
    def validate_sector_site(self) -> "InternalInferenceRequest":
        valid_sites = {
            "energy": {"control_centre", "substation"},
            "petrochemical": {"refinery", "petrochemical_complex"},
        }
        if self.site_type not in valid_sites[self.industry]:
            raise ValueError(
                f"site_type {self.site_type!r} is invalid for "
                f"industry {self.industry!r}"
            )
        return self


class InternalInferenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    task: Literal["RW-100-6"]
    mode: Literal["synthetic_scenario"]
    request_id: str
    trace_id: str
    scenario_id: str
    bundle_version: str
    result: dict[str, Any]
    runtime_contract: dict[str, Any]


def _development_rows():
    _, frozen = load_and_verify_scenarios()
    rows, feature_names = build_rows(frozen)
    development_rows = [
        row for row in rows if row.split in DEVELOPMENT_SPLITS
    ]
    if not development_rows:
        raise ValueError("No development rows available")
    return frozen, rows, feature_names, development_rows


@lru_cache(maxsize=1)
def _runtime_context():
    frozen, rows, feature_names, development_rows = _development_rows()

    baseline = RobustAnomalyBaseline(
        feature_names,
        random_state=20260921,
    )
    baseline.fit(row.features for row in development_rows)

    scenarios = {
        scenario.scenario_id: scenario
        for scenario in frozen
    }

    rows_by_key = {
        (row.scenario_id, row.window_minutes): row
        for row in rows
    }

    return scenarios, rows_by_key, baseline


def _score_scenario(
    request: InternalInferenceRequest,
) -> dict[str, Any]:
    scenarios, rows_by_key, anomaly = _runtime_context()

    scenario = scenarios.get(request.scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown frozen scenario_id: {request.scenario_id}",
        )

    if scenario.industry != request.industry:
        raise HTTPException(
            status_code=422,
            detail="scenario industry does not match request industry",
        )

    scenario_site_types = set(scenario.site_types)
    if request.site_type not in scenario_site_types:
        raise HTTPException(
            status_code=422,
            detail="scenario site_type does not match request site_type",
        )

    # Synthetic scenario mode uses the frozen observable event stream only.
    # Truth-bearing scenario fields remain internal and are never passed to
    # canonical inference or returned by the API.
    row = rows_by_key[(request.scenario_id, 1)]
    events = assemble_scenario_events(scenario)

    if not events:
        raise HTTPException(
            status_code=422,
            detail="scenario produced no observable events",
        )

    end_time = events[-1].event_time.replace("Z", "+00:00")

    from datetime import datetime

    end_datetime = datetime.fromisoformat(end_time)

    rule_score = _rule_score(row.features)
    anomaly_evidence = anomaly.score(row.features)
    anomaly_score = _anomaly_score(anomaly_evidence)
    graph_score, graph_exposed_count = _graph_score(
        request.industry,
        events,
        end_datetime,
        row.window_minutes,
    )

    canonical = canonical_inference(
        observable_features=row.features,
        industry=request.industry,
        site_types="|".join(sorted(scenario.site_types)),
        rule_score=rule_score,
        anomaly_score=anomaly_score,
        graph_score=graph_score,
        sector=request.industry,
    )

    canonical["components"]["graph_exposed_asset_count"] = graph_exposed_count
    canonical["components"]["graph_status"] = (
        "deterministic_weighted_propagation"
    )
    canonical["components"]["temporal_status"] = (
        "unavailable_rejected_challenger"
    )

    return canonical


app = FastAPI(
    title="Ransomware Resilience Internal ML API",
    version=API_SCHEMA_VERSION,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "task": TASK_ID,
        "schema_version": API_SCHEMA_VERSION,
    }


@app.post(
    "/internal/ransomware/infer",
    response_model=InternalInferenceResponse,
)
def infer(request: InternalInferenceRequest) -> InternalInferenceResponse:
    request_id = str(uuid4())
    trace_id = str(uuid4())

    result = _score_scenario(request)

    return InternalInferenceResponse(
        schema_version=API_SCHEMA_VERSION,
        task=TASK_ID,
        mode=MODE,
        request_id=request_id,
        trace_id=trace_id,
        scenario_id=request.scenario_id,
        bundle_version=result["bundle_version"],
        result=result,
        runtime_contract=result["runtime_contract"],
    )


def main() -> None:
    print("=== RW-100-6 INTERNAL ML API ===")
    print(f"Schema version: {API_SCHEMA_VERSION}")
    print(f"Endpoint: POST /internal/ransomware/infer")
    print(f"Mode: {MODE}")
    print("Frontend direct access: forbidden by architecture")
