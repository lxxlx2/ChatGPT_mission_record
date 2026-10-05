import pytest

from mission_agent.mission_control.jupiter import JupiterQuoteClient
from mission_agent.mission_control.server import serve


def test_missing_jupiter_key_fails_closed_without_network():
    client = JupiterQuoteClient(None, open_url=lambda *a,**k: pytest.fail("network must not be used"))
    result = client.quote_usdc_to_token("Mint111", 6)
    assert result["status"] == "UNAVAILABLE"
    assert result["reason"] == "JUPITER_API_KEY_NOT_CONFIGURED"


def test_dashboard_refuses_public_bind(tmp_path):
    with pytest.raises(ValueError, match="MISSION_CONTROL_LOCALHOST_ONLY"):
        serve(tmp_path / "prod", tmp_path / "control", host="0.0.0.0", port=9999)
