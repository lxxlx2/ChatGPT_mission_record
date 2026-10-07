import io
import json
import urllib.error

import pytest

import mission_agent.mission_control.jupiter as jupiter_module
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


def test_keyless_jupiter_quote_uses_network_without_auth_header():
    seen=[]
    body={"outAmount":"1000000","routePlan":[{"swapInfo":{}}],"priceImpactPct":"0.001"}

    def open_url(request,timeout=8):
        seen.append(request)
        return FakeResponse(json.dumps(body).encode())

    client=JupiterQuoteClient(None,open_url=open_url,minimum_interval_seconds=0)
    result=client.quote_usdc_to_token("Mint111",6)
    assert result["status"]=="OK"
    assert result["route_exists"] is True
    assert result["price_impact_pct"]=="0.100"
    headers={k.lower():v for k,v in seen[0].header_items()}
    assert "x-api-key" not in headers


def test_jupiter_default_throttle_has_keyless_headroom_and_cooldown():
    keyless=JupiterQuoteClient(None)
    keyed=JupiterQuoteClient("key")
    assert keyless.minimum_interval_seconds==2.5
    assert keyed.minimum_interval_seconds==1.05
    assert keyless.rate_limit_cooldown_seconds==10.0
    assert keyed.rate_limit_cooldown_seconds==5.0


def test_keyed_jupiter_quote_sends_auth_header():
    seen=[]
    body={"outAmount":"1000000","routePlan":[{"swapInfo":{}}],"priceImpactPct":"0.001"}

    def open_url(request,timeout=8):
        seen.append(request)
        return FakeResponse(json.dumps(body).encode())

    client=JupiterQuoteClient("key",open_url=open_url,minimum_interval_seconds=0)
    result=client.quote_usdc_to_token("Mint111",6)
    assert result["status"]=="OK"
    headers={k.lower():v for k,v in seen[0].header_items()}
    assert headers["x-api-key"]=="key"


def test_jupiter_429_sets_cooldown_before_next_request(monkeypatch):
    body={"outAmount":"1000000","routePlan":[{"swapInfo":{}}],"priceImpactPct":"0.001"}
    calls={"count":0}
    sleeps=[]

    def open_url(request,timeout=8):
        calls["count"]+=1
        if calls["count"]==1:
            raise urllib.error.HTTPError(
                request.full_url,
                429,
                "rate limited",
                {"Retry-After":"12"},
                io.BytesIO(b'{}'),
            )
        return FakeResponse(json.dumps(body).encode())

    monkeypatch.setattr(jupiter_module.time,"monotonic",lambda:100.0)
    monkeypatch.setattr(jupiter_module.time,"sleep",lambda seconds:sleeps.append(seconds))
    client=JupiterQuoteClient(
        None,
        open_url=open_url,
        minimum_interval_seconds=0,
        rate_limit_cooldown_seconds=10,
    )
    first=client.quote_usdc_to_token("Mint111",6)
    second=client.quote_usdc_to_token("Mint111",6)
    assert first["status"]=="UNAVAILABLE"
    assert first["reason"]=="JUPITER_RATE_LIMITED"
    assert second["status"]=="OK"
    assert sleeps and sleeps[-1]>=12.0


def test_jupiter_retry_after_is_capped_at_60_seconds(monkeypatch):
    body={"outAmount":"1000000","routePlan":[{"swapInfo":{}}],"priceImpactPct":"0.001"}
    calls={"count":0}
    sleeps=[]

    def open_url(request,timeout=8):
        calls["count"]+=1
        if calls["count"]==1:
            raise urllib.error.HTTPError(
                request.full_url,
                429,
                "rate limited",
                {"Retry-After":"3600"},
                io.BytesIO(b'{}'),
            )
        return FakeResponse(json.dumps(body).encode())

    monkeypatch.setattr(jupiter_module.time,"monotonic",lambda:100.0)
    monkeypatch.setattr(jupiter_module.time,"sleep",lambda seconds:sleeps.append(seconds))
    client=JupiterQuoteClient(
        None,
        open_url=open_url,
        minimum_interval_seconds=0,
        rate_limit_cooldown_seconds=10,
    )
    first=client.quote_usdc_to_token("Mint111",6)
    second=client.quote_usdc_to_token("Mint111",6)
    assert first["status"]=="UNAVAILABLE"
    assert first["reason"]=="JUPITER_RATE_LIMITED"
    assert second["status"]=="OK"
    assert sleeps and sleeps[-1]==60.0


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


def test_jupiter_reverse_quote_measures_same_token_raw_back_to_usdc():
    seen=[]
    body={"outAmount":"36000000","routePlan":[{"swapInfo":{}}],"priceImpactPct":"0.004"}
    client=JupiterQuoteClient(None,open_url=responder(body,seen),minimum_interval_seconds=0)
    result=client.quote_token_to_usdc("Mint111","30000000",6)
    assert result["status"]=="OK"
    assert result["route_exists"] is True
    assert result["out_usdc"]=="36"
    assert result["execution_price_usdc"]=="1.2"
    assert result["price_impact_pct"]=="0.400"
    assert "inputMint=Mint111" in seen[0]
    assert "outputMint="+jupiter_module.USDC in seen[0]
    assert "amount=30000000" in seen[0]
