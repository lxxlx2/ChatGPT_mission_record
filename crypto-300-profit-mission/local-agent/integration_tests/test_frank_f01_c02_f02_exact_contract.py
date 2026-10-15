"""F01+C02+F02 integrated services, isolated synthetic complete wire, no RPC.

This test runs ONLY in disposable combined checkout (F01/C02 independent PRs).
No production inputs, no network, no new jobs or server deployment.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time

from mission_agent.meme.identity import reconcile_identity
from mission_agent.mission_control.follow_view import partition_candidates
from mission_agent.mission_control.frank_ca_f02_alignment import align_frank_ca_f02
from mission_agent.mission_control.wallet_chain_capture import (
    SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM,
)
from scripts.frank_f02_manual_refresh import refresh_session
from scripts.frank_reconcile_frozen32_offline import load_frozen_roster, ROSTER

WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
ACCOUNTS = ("2MzJd4RG5F8H1BQx37K9dSTcaLtiwwsgZUgBMQHtGrPH",
            "9YUxkbLmyY1nxwEtZmNHUTzwzVjBAUwyuXiSzpHJ1sRn")


def synthetic_read(owner, mint, account, program, raw):
    return {"pubkey": account, "account": {
        "owner": program,
        "data": {"parsed": {"type": "account", "info": {
            "owner": owner, "mint": mint, "state": "initialized",
            "tokenAmount": {"amount": raw, "decimals": 6},
        }}},
    }}


def test_same_exact_ca_crosses_real_F01_C02_and_F02_without_live_network(tmp_path):
    targets = load_frozen_roster(ROSTER, WALLET)["records"]
    mint = targets[0]["mint"]
    other = targets[1]["mint"]
    calls = []

    def local_wire(method, params, ident):
        calls.append((method, ident))
        program = SPL_TOKEN_PROGRAM if ident == 1 else TOKEN_2022_PROGRAM
        obj = synthetic_read(WALLET, targets[ident - 1]["mint"],
                             ACCOUNTS[ident - 1], program,
                             "123000000" if ident == 1 else "0")
        return json.dumps({
            "jsonrpc": "2.0", "id": ident,
            "result": {"context": {"slot": 5000 + ident}, "value": [obj]},
        }).encode()

    session, service = refresh_session(
        session_root=tmp_path / "private-synthetic", read_raw=local_wire)
    assert session["status"] == "VERIFIED_MANUAL_RESEARCH_SESSION"
    assert calls == [("getTokenAccountsByOwner", 1),
                     ("getTokenAccountsByOwner", 2)]
    original_bytes = Path(session["sidecar"]).read_bytes()
    fresh = service.positions()
    assert fresh["readiness"] == "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
    assert fresh["target_mint_count"] == 32
    assert fresh["mints"][0]["mint"] == mint

    now = time.time()
    candidate = {
        "mint": mint, "person_id": "frank", "decision": "BUY",
        "source_signal_id": "frozen-synthetic-1", "pattern": "MULTIPLE",
        "episode_id": "sample", "position_state": "OPEN",
        "current_raw": "123000000", "latest_side": "BUY",
        "latest_at": now - 10, "latest_buy_at": now - 10,
        "decision_created_at": now - 2, "quote_observed_at": now - 3,
        "decision_quote": {"status": "OK", "route_exists": True},
        "metrics": {"execution_price_usdc": "0.1", "price_impact_pct": "0.1"},
    }
    f01 = partition_candidates([candidate], now=now,
                               runtime_status="LIVE",
                               max_frank_buy_age_seconds=600,
                               max_quote_age_seconds=30)
    assert f01["eligible_count"] == 1

    token_profile = {"mint": mint, "status": "OK", "mint_account_status": "VERIFIED",
                     "metadata": {"status": "VERIFIED", "records": [{
                         "mint": mint, "name": "Collision", "symbol": "COL",
                         "source": "TOKEN2022_METADATA", "update_authority": None,
                     }]}}
    market = {"mint": mint, "status": "OK",
              "market_match_status": "EXACT_BASE_MINT_MATCH",
              "identity_records": [{"mint": mint, "name": "Collision",
                                    "symbol": "COL", "source": "DEXSCREENER_API"}]}
    identity = reconcile_identity(mint, token_profile, market)
    assert identity["identity_status"] == "VERIFIED"
    assert identity["conflict_status"] == "NO_CONFLICT_OBSERVED"
    c02 = {"mint": mint, "chain": "solana",
           "token_identity": identity,
           "assessment": {"narrative_status": "NOT_AUTOMATICALLY_VERIFIED"}}

    out = align_frank_ca_f02(mint=mint, follow=f01, ca_report=c02,
                              f02_positions=fresh)
    assert out["f01"]["status"] == "F01_ELIGIBLE"
    assert out["f02"]["state"] == "OPEN_ACCOUNT_NONZERO"
    assert out["f02"]["observed_quantity"] == "123.000000"
    assert out["c02"]["status"] == "CA_EXACT_MINT_IDENTITY_VERIFIED"
    assert out["c02"]["narrative_status"] == "NOT_AUTOMATICALLY_VERIFIED"
    assert out["combined_trade_permission"] is False

    # Same token NAME must not join an entirely distinct contract.
    unrelated = align_frank_ca_f02(mint=other, follow=f01, ca_report=c02,
                                    f02_positions=fresh)
    assert unrelated["f01"]["status"] == "F01_NOT_ELIGIBLE"
    assert unrelated["c02"]["status"] == "CA_MINT_MISMATCH"
    assert unrelated["f02"]["state"] == "OPEN_ACCOUNT_ZERO"
    assert unrelated["combined_trade_permission"] is False

    after_sell = partition_candidates([{**candidate, "latest_side": "SELL"}],
                                      now=now, runtime_status="LIVE",
                                      max_frank_buy_age_seconds=600,
                                      max_quote_age_seconds=30)
    assert after_sell["eligible_count"] == 0
    deny = align_frank_ca_f02(mint=mint, follow=after_sell, ca_report=c02,
                               f02_positions=fresh)
    assert deny["f01"]["status"] == "F01_NOT_ELIGIBLE"

    old_capture = datetime.fromisoformat(fresh["capture_observed_at_utc"])
    stale = service.positions(as_of_utc=old_capture + timedelta(seconds=301))
    assert stale["readiness"] == "STALE_ARCHIVED_SOURCE"
    unavailable = align_frank_ca_f02(mint=mint, follow=f01, ca_report=c02,
                                      f02_positions=stale)
    assert unavailable["f01"]["status"] == "F01_ELIGIBLE"
    assert unavailable["f02"]["state"] == "SOURCE_UNAVAILABLE"
    assert unavailable["f02"]["observed_quantity"] is None
    assert unavailable["combined_trade_permission"] is False

    assert Path(session["sidecar"]).read_bytes() == original_bytes
    assert len(calls) == 2
