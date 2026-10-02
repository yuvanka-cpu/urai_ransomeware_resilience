from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


INCIDENT_STAGES = (
    "none",
    "precursor",
    "credential_misuse",
    "lateral_movement",
    "staging",
    "encryption_impact",
    "recovery",
)

SEVERITIES = (
    "low",
    "medium",
    "high",
    "critical",
)

DATA_PROVENANCE = (
    "LIVE_MODEL",
    "SYNTHETIC_GROUND_TRUTH",
    "STATIC_SCENARIO_METADATA",
    "DERIVED_BY_BACKEND",
    "FALLBACK",
    "UNAVAILABLE",
)


@dataclass
class RansomwareResult:
    use_case: str
    industry: str
    site_id: str
    site_type: str
    decision: str
    incident_stage: str
    confidence: float
    severity: str
    resilience_score: int | None = None
    resilience_score_method: str | None = None
    affected_assets: list[str] = field(default_factory=list)
    suspected_assets: list[str] = field(default_factory=list)
    critical_services_at_risk: list[str] = field(default_factory=list)
    affected_zones: list[str] = field(default_factory=list)
    protected_boundaries: list[str] = field(default_factory=list)
    operational_dependency_impact: list[str] = field(default_factory=list)
    propagation_path: list[str] = field(default_factory=list)
    evidence_layers: list[dict[str, Any]] = field(default_factory=list)
    triggered_rules: list[dict[str, Any]] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    backup_readiness: dict[str, Any] = field(default_factory=dict)
    explanations: list[str] = field(default_factory=list)
    recommended_actions: list[dict[str, Any]] = field(default_factory=list)
    human_approval_required: bool = True
    real_action_executed: bool = False
    artifact_provenance: list[dict[str, Any]] = field(default_factory=list)
    data_provenance: str = "LIVE_MODEL"
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.incident_stage not in INCIDENT_STAGES:
            raise ValueError(
                f"Invalid incident_stage: {self.incident_stage}"
            )

        if self.severity not in SEVERITIES:
            raise ValueError(f"Invalid severity: {self.severity}")

        if self.data_provenance not in DATA_PROVENANCE:
            raise ValueError(
                f"Invalid data_provenance: {self.data_provenance}"
            )

        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if self.affected_assets and self.suspected_assets:
            overlap = set(self.affected_assets) & set(self.suspected_assets)
            if overlap:
                raise ValueError(
                    f"Assets cannot be both affected and suspected: {sorted(overlap)}"
                )

        if self.real_action_executed is not False:
            raise ValueError("real_action_executed must remain false")

        if self.human_approval_required is not True:
            raise ValueError("human_approval_required must remain true")

    def to_dict(self) -> dict[str, Any]:
        return {
            "use_case": self.use_case,
            "industry": self.industry,
            "site_id": self.site_id,
            "site_type": self.site_type,
            "decision": self.decision,
            "incident_stage": self.incident_stage,
            "confidence": float(self.confidence),
            "severity": self.severity,
            "resilience_score": self.resilience_score,
            "resilience_score_method": self.resilience_score_method,
            "affected_assets": list(self.affected_assets),
            "suspected_assets": list(self.suspected_assets),
            "critical_services_at_risk": list(self.critical_services_at_risk),
            "affected_zones": list(self.affected_zones),
            "protected_boundaries": list(self.protected_boundaries),
            "operational_dependency_impact": list(
                self.operational_dependency_impact
            ),
            "propagation_path": list(self.propagation_path),
            "evidence_layers": list(self.evidence_layers),
            "triggered_rules": list(self.triggered_rules),
            "timeline": list(self.timeline),
            "backup_readiness": dict(self.backup_readiness),
            "explanations": list(self.explanations),
            "recommended_actions": list(self.recommended_actions),
            "human_approval_required": True,
            "real_action_executed": False,
            "artifact_provenance": list(self.artifact_provenance),
            "data_provenance": self.data_provenance,
            "warnings": list(self.warnings),
        }


def assemble_result(
    *,
    use_case: str,
    industry: str,
    site_id: str,
    site_type: str,
    decision: str,
    confidence: float,
    incident_stage: str,
    severity: str,
    **context: Any,
) -> dict[str, Any]:
    result = RansomwareResult(
        use_case=use_case,
        industry=industry,
        site_id=site_id,
        site_type=site_type,
        decision=decision,
        confidence=confidence,
        incident_stage=incident_stage,
        severity=severity,
        **context,
    )

    return result.to_dict()


def main() -> None:
    print("=== RW-100-4 RESULT ASSEMBLY ===")
    print(f"Incident stages: {len(INCIDENT_STAGES)}")
    print(f"Severity levels: {len(SEVERITIES)}")
    print(f"Provenance labels: {len(DATA_PROVENANCE)}")
    print("Human approval required: True")
    print("Real action executed: False")
    print("Status: result contract ready")


if __name__ == "__main__":
    main()


def assemble_canonical_result(
    *,
    canonical_inference: dict[str, Any],
    use_case: str,
    site_id: str,
    site_type: str,
    incident_stage: str,
    severity: str,
    affected_assets: list[str] | None = None,
    suspected_assets: list[str] | None = None,
    critical_services_at_risk: list[str] | None = None,
    affected_zones: list[str] | None = None,
    protected_boundaries: list[str] | None = None,
    operational_dependency_impact: list[str] | None = None,
    propagation_path: list[str] | None = None,
    evidence_layers: list[dict[str, Any]] | None = None,
    triggered_rules: list[dict[str, Any]] | None = None,
    timeline: list[dict[str, Any]] | None = None,
    backup_readiness: dict[str, Any] | None = None,
    explanations: list[str] | None = None,
    recommended_actions: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    probabilities = canonical_inference["probabilities"]
    runtime_contract = canonical_inference["runtime_contract"]

    return assemble_result(
        use_case=use_case,
        industry=canonical_inference["sector"],
        site_id=site_id,
        site_type=site_type,
        decision=canonical_inference["decision"],
        confidence=float(probabilities["calibrated"]),
        incident_stage=incident_stage,
        severity=severity,
        affected_assets=affected_assets or [],
        suspected_assets=suspected_assets or [],
        critical_services_at_risk=critical_services_at_risk or [],
        affected_zones=affected_zones or [],
        protected_boundaries=protected_boundaries or [],
        operational_dependency_impact=operational_dependency_impact or [],
        propagation_path=propagation_path or [],
        evidence_layers=evidence_layers or [],
        triggered_rules=triggered_rules or [],
        timeline=timeline or [],
        backup_readiness=backup_readiness or {},
        explanations=explanations or [],
        recommended_actions=recommended_actions or [],
        artifact_provenance=[
            {
                "bundle_version": canonical_inference["bundle_version"],
                "task": canonical_inference["task"],
            }
        ],
        data_provenance="LIVE_MODEL",
        warnings=warnings or [],
        human_approval_required=runtime_contract["human_approval_required"],
        real_action_executed=runtime_contract["real_action_executed"],
    )
