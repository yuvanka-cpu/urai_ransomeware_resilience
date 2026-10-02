import httpx
import pytest

from app.services import ransomware_ml_gateway as gateway


PAYLOAD = {
    "schema_version": "1.0",
    "mode": "synthetic_scenario",
    "industry": "energy",
    "site_id": "synthetic-site-001",
    "site_type": "control_centre",
    "scenario_id": "rw-stage11-route-contract",
    "observable_input": {},
}


def test_rw1103_gateway_maps_timeout(monkeypatch):
    class TimeoutClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            raise httpx.ReadTimeout("synthetic timeout")

    monkeypatch.setattr(gateway.httpx, "Client", TimeoutClient)

    with pytest.raises(
        gateway.MLGatewayError,
        match="timeout after retry policy",
    ):
        gateway.call_ml_service(PAYLOAD, max_retries=1)


def test_rw1103_gateway_maps_dependency_failure(monkeypatch):
    class FailureClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            raise httpx.ConnectError("synthetic connection failure")

    monkeypatch.setattr(gateway.httpx, "Client", FailureClient)

    with pytest.raises(
        gateway.MLGatewayError,
        match="dependency unavailable",
    ):
        gateway.call_ml_service(PAYLOAD, max_retries=1)


def test_rw1103_gateway_maps_http_500(monkeypatch):
    class Response:
        status_code = 500
        text = "synthetic ML failure"

    class FailureClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr(gateway.httpx, "Client", FailureClient)

    with pytest.raises(
        gateway.MLGatewayError,
        match="dependency failure",
    ):
        gateway.call_ml_service(PAYLOAD, max_retries=1)
