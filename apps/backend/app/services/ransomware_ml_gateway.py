import os
import time
from typing import Any

import httpx


ML_SERVICE_URL = os.getenv(
    "RANSOMWARE_ML_SERVICE_URL",
    "http://127.0.0.1:8001",
).rstrip("/")
ML_ENDPOINT = f"{ML_SERVICE_URL}/internal/ransomware/infer"

DEFAULT_TIMEOUT_SECONDS = 1.0
MAX_RETRIES = 1


class MLGatewayError(RuntimeError):
    pass


def call_ml_service(
    payload: dict[str, Any],
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = MAX_RETRIES,
    request_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            started = time.perf_counter()

            headers: dict[str, str] = {}
            if request_id:
                headers["X-Request-ID"] = request_id
            if trace_id:
                headers["X-Trace-ID"] = trace_id

            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(
                    ML_ENDPOINT,
                    json=payload,
                    headers=headers,
                )

            latency_ms = (time.perf_counter() - started) * 1000.0

            if response.status_code >= 500:
                raise MLGatewayError(
                    f"ML service dependency failure: HTTP {response.status_code}"
                )

            if response.status_code >= 400:
                raise MLGatewayError(
                    "ML service rejected request: "
                    f"HTTP {response.status_code}: {response.text}"
                )

            body = response.json()

            if not isinstance(body, dict):
                raise MLGatewayError(
                    "ML service returned a non-object response"
                )

            body["_gateway_latency_ms"] = round(latency_ms, 3)
            body["_gateway_attempt"] = attempt + 1
            body["_gateway_request_id"] = request_id
            body["_gateway_trace_id"] = trace_id

            return body

        except (
            httpx.TimeoutException,
            httpx.RequestError,
            MLGatewayError,
        ) as exc:
            last_error = exc

            if attempt < max_retries:
                continue

            if isinstance(exc, httpx.TimeoutException):
                raise MLGatewayError(
                    "ML service timeout after retry policy"
                ) from exc

            if isinstance(exc, httpx.RequestError):
                raise MLGatewayError(
                    f"ML service dependency unavailable: {exc}"
                ) from exc

            raise

    raise MLGatewayError("ML gateway failed") from last_error
