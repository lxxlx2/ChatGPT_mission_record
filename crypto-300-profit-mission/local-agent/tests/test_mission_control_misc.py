import io
import json

import pytest

from mission_agent.mission_control.frank import _pid_alive
from mission_agent.mission_control.jupiter import JupiterQuoteClient
from mission_agent.mission_control.server import _host_header_is_loopback, serve


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()
        return False


def responder(payload, seen=None):
    def open_url(request, timeout=8):
        if seen is not None:
            seen.append(request.full_url)
        return FakeResponse(json.dumps(payload).encode())
    return open_url


def test_missing_jupiter_key_fails_closed_without_network():
    client = JupiterQuoteClient(None, open_url=lambda *a,**k: pytest.fail("network must not be used"))
    result = client.quote_usdc_to_token("Mint111", 6)
    assert result["status"] == "UNAVAILABLE"
    assert result["reason"] == "JUPITER_API_KEY_NOT_CONFIGURED"


def test_jupiter_missing_price_impact_fails_closed():
    body={"outAmount":"1000000","routePlan":[{"swapInfo":{}}]}
    client=JupiterQuoteClient("key",open_url=responder(body),minimum_interval_seconds=0)
    result=client.quote_usdc_to_token("Mint111",6)
    assert result["status"]=="UNAVAILABLE"
    assert result["reason"]=="JUPITER_PRICE_IMPACT_MISSING"


def test_jupiter_explicit_no_route_is_reachable_no_buy_input():
    body={"error":"Could not find any route"}
    client=JupiterQuoteClient("key",open_url=responder(body),minimum_interval_seconds=0)
    result=client.quote_usdc_to_token("Mint111",6)
    assert result["status"]=="OK"
    assert result["route_exists"] is False
    assert result["reason"]=="JUPITER_NO_ROUTE"


def test_jupiter_quote_does_not_send_instruction_version_parameter():
    seen=[]
    body={"outAmount":"1000000","routePlan":[{"swapInfo":{}}],"priceImpactPct":"0.001"}
    client=JupiterQuoteClient("key",open_url=responder(body,seen),minimum_interval_seconds=0)
    result=client.quote_usdc_to_token("Mint111",6)
    assert result["status"]=="OK"
    assert "instructionVersion" not in seen[0]
    assert result["price_impact_pct"]=="0.100"


def test_bad_pid_value_fails_closed_instead_of_crashing():
    assert _pid_alive("not-a-pid") is False


def test_dashboard_refuses_public_bind(tmp_path):
    with pytest.raises(ValueError, match="MISSION_CONTROL_LOCALHOST_ONLY"):
        serve(tmp_path / "prod", tmp_path / "control", host="0.0.0.0", port=9999)


def test_dashboard_host_header_gate_accepts_only_loopback_values():
    assert _host_header_is_loopback("127.0.0.1:8765") is True
    assert _host_header_is_loopback("localhost:8765") is True
    assert _host_header_is_loopback("[::1]:8765") is True
    assert _host_header_is_loopback("example.com:8765") is False
