from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import median
from typing import Iterable, Mapping, Sequence

from sklearn.ensemble import IsolationForest


DEFAULT_Z_THRESHOLD = 3.5
DEFAULT_ISOLATION_CONTAMINATION = "auto"
DEFAULT_ISOLATION_ESTIMATORS = 100
DEFAULT_RANDOM_STATE = 42


@dataclass(frozen=True)
class BaselineEvidence:
    univariate_triggered: bool
    univariate_evidence_count: int
    multivariate_triggered: bool
    multivariate_score: float
    multivariate_threshold: float
    isolation_triggered: bool
    isolation_score: float
    explanation: str


class RobustAnomalyBaseline:
    """Deterministic anomaly evidence baseline.

    This class emits anomaly evidence only. It does not assign an incident
    decision, severity, confidence, or response action.
    """

    def __init__(
        self,
        feature_names: Sequence[str],
        *,
        z_threshold: float = DEFAULT_Z_THRESHOLD,
        n_estimators: int = DEFAULT_ISOLATION_ESTIMATORS,
        contamination: str = DEFAULT_ISOLATION_CONTAMINATION,
        random_state: int = DEFAULT_RANDOM_STATE,
    ) -> None:
        if not feature_names:
            raise ValueError("feature_names must not be empty")

        if z_threshold <= 0:
            raise ValueError("z_threshold must be positive")

        if n_estimators <= 0:
            raise ValueError("n_estimators must be positive")

        if len(set(feature_names)) != len(feature_names):
            raise ValueError("feature_names must be unique")

        self.feature_names = tuple(feature_names)
        self.z_threshold = float(z_threshold)
        self.multivariate_threshold = (
            self.z_threshold * sqrt(len(self.feature_names))
        )
        self.isolation = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
        )

        self._medians: dict[str, float] | None = None
        self._scales: dict[str, float] | None = None
        self._fitted = False

    @staticmethod
    def _mad(values: Sequence[float], center: float) -> float:
        return median(abs(value - center) for value in values)

    def fit(
        self,
        rows: Iterable[Mapping[str, float | int]],
    ) -> "RobustAnomalyBaseline":
        materialized = [dict(row) for row in rows]

        if len(materialized) < 2:
            raise ValueError("at least two training rows are required")

        missing = {
            field
            for row in materialized
            for field in self.feature_names
            if field not in row
        }
        if missing:
            raise ValueError(
                "missing required features: " + ", ".join(sorted(missing))
            )

        medians: dict[str, float] = {}
        scales: dict[str, float] = {}

        for field in self.feature_names:
            values = [float(row[field]) for row in materialized]
            centre = float(median(values))
            mad = float(self._mad(values, centre))
            scale = 1.4826 * mad

            if scale == 0.0:
                scale = 1.0

            medians[field] = centre
            scales[field] = scale

        matrix = [
            [float(row[field]) for field in self.feature_names]
            for row in materialized
        ]

        self._medians = medians
        self._scales = scales
        self.isolation.fit(matrix)
        self._fitted = True

        return self

    def _robust_z_scores(
        self,
        row: Mapping[str, float | int],
    ) -> list[float]:
        if not self._fitted or self._medians is None or self._scales is None:
            raise RuntimeError("baseline must be fitted before scoring")

        missing = [
            field
            for field in self.feature_names
            if field not in row
        ]
        if missing:
            raise ValueError(
                "missing required features: " + ", ".join(missing)
            )

        return [
            abs(
                (
                    float(row[field]) - self._medians[field]
                )
                / self._scales[field]
            )
            for field in self.feature_names
        ]

    def score(
        self,
        row: Mapping[str, float | int],
    ) -> BaselineEvidence:
        z_scores = self._robust_z_scores(row)

        univariate_evidence_count = sum(
            score >= self.z_threshold
            for score in z_scores
        )
        univariate_triggered = univariate_evidence_count > 0

        multivariate_score = sqrt(
            sum(score * score for score in z_scores)
        )
        multivariate_triggered = (
            multivariate_score >= self.multivariate_threshold
        )

        vector = [[float(row[field]) for field in self.feature_names]]
        isolation_prediction = int(self.isolation.predict(vector)[0])
        isolation_score = float(
            -self.isolation.score_samples(vector)[0]
        )
        isolation_triggered = isolation_prediction == -1

        triggered_sources = []
        if univariate_triggered:
            triggered_sources.append("univariate")
        if multivariate_triggered:
            triggered_sources.append("multivariate")
        if isolation_triggered:
            triggered_sources.append("isolation_forest")

        if triggered_sources:
            explanation = (
                "Anomaly evidence triggered by: "
                + ", ".join(triggered_sources)
                + ". This output is evidence only and does not assign a "
                "final incident decision."
            )
        else:
            explanation = (
                "No anomaly threshold triggered. This output is evidence "
                "only and does not assign a final incident decision."
            )

        return BaselineEvidence(
            univariate_triggered=univariate_triggered,
            univariate_evidence_count=univariate_evidence_count,
            multivariate_triggered=multivariate_triggered,
            multivariate_score=round(multivariate_score, 6),
            multivariate_threshold=round(
                self.multivariate_threshold,
                6,
            ),
            isolation_triggered=isolation_triggered,
            isolation_score=round(isolation_score, 6),
            explanation=explanation,
        )
