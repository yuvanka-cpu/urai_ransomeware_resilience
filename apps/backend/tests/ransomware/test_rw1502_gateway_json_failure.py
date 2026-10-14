"""RW-150-2: Malformed ML service JSON must fail safely."""

from unittest.mock import patch

import httpx
import pytest

from app.services.ransomware_ml_gateway import (
    MLGatewayError,
    call_ml_service,
)


def test_rw1502_malformed_json_raises_gateway_error():
    request = httpx.Request(
        "POST",
        "http://127.0.0.1:8001/internal/ransomware/infer",
    )

    malformed_response = httpx.Response(
        200,
        content=b'{"result": invalid-json}',
        request=request,
    )

    with patch(
        "app.services.ransomware_ml_gateway.httpx.Client"
    ) as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = (
            malformed_response
        )

        with pytest.raises(
            MLGatewayError,
            match="invalid JSON",
        ):
            call_ml_service(
                {
                    "schema_version": "1.0",
                    "mode": "synthetic_scenario",
                },
                max_retries=0,
            )
