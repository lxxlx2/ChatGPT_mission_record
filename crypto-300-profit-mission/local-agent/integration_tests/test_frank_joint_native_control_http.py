"""Three actual route handlers, real F01/C02 functions, synthetic source F02.

Executed in disposable combined F01+C02+F02 checkout only. Never connects to
Solana, user Mac/production DB, or starts a background auto research job.
"""
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time

from mission_agent.meme.identity import reconcile_identity
from mission_agent.mission_control.follow_view import partition_candidates
from mission_agent.mission_control.server import Handler as NativeControlHandler
from mission_agent.mission_control.wallet_chain_capture import (
    SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM,
)
from scripts.frank_f02_manual_refresh import refresh_session
from scripts.frank_f02_readonly_positions_api import make_handler as f02_handler
from scripts.frank_joint_readonly_http import JointReadOnly, make_handler
from scripts.frank_reconcile_frozen32_offline import (
    ROSTER, load_frozen_roster,
)
from test_frank_a04_a05_chain_capture import entry, pk

WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"


@contextmanager
def serve_once(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_real_native_F01_C02_and_F02_handler_get_join_no_hidden_posts(tmp_path):
    targets = load_frozen_roster(ROSTER, WALLET)["records"]
    mint, zero = targets[0]["mint"], targets[1]["mint"]
    rpc_calls = []

    def synthetic_wire(method, params, ident):
        rpc_calls.append((method, ident))
        program = SPL_TOKEN_PROGRAM if ident == 1 else TOKEN_2022_PROGRAM
        wire_entry = entry(WALLET, targets[ident - 1]["mint"],
                           pk(90 + ident), program,
                           amount="123000000" if ident == 1 else "0")
        return json.dumps({
            "jsonrpc": "2.0", "id": ident,
            "result": {"context": {"slot": 5000 + ident},
                       "value": [wire_entry]},
        }).encode()

    session, f02_service = refresh_session(
        session_root=tmp_path / "synthetic-sessions",
        read_raw=synthetic_wire)
    assert session["status"] == "VERIFIED_MANUAL_RESEARCH_SESSION"
    before = Path(session["sidecar"]).read_bytes()
    assert rpc_calls == [("getTokenAccountsByOwner", 1),
                         ("getTokenAccountsByOwner", 2)]

    now = time.time()
    candidate = {
        "mint": mint, "person_id": "frank", "decision": "BUY",
        "source_signal_id": "synthetic-qualified-signal",
        "pattern": "MULTIPLE", "episode_id": "sample",
        "position_state": "OPEN", "current_raw": "123000000",
        "latest_side": "BUY", "latest_at": now - 10,
        "latest_buy_at": now - 10, "decision_created_at": now - 2,
        "quote_observed_at": now - 2,
        "decision_quote": {"status": "OK", "route_exists": True,
                           "execution_price_usdc": "0.1",
                           "price_impact_pct": "0.1"},
        "metrics": {"execution_price_usdc": "0.1",
                    "price_impact_pct": "0.1"},
    }
    follow = partition_candidates(
        [candidate], now=now, runtime_status="LIVE",
        max_frank_buy_age_seconds=600, max_quote_age_seconds=30)
    assert follow["eligible_count"] == 1

    token_profile = {
        "mint": mint, "status": "OK", "mint_account_status": "VERIFIED",
        "metadata": {"status": "VERIFIED", "records": [{
            "mint": mint, "name": "Proof token",
            "symbol": "PRF", "source": "TOKEN2022_METADATA",
            "update_authority": None,
        }]},
    }
    market = {
        "mint": mint, "status": "OK",
        "market_match_status": "EXACT_BASE_MINT_MATCH",
        "identity_records": [{
            "mint": mint, "name": "Proof token", "symbol": "PRF",
            "source": "DEXSCREENER_API",
        }],
    }
    identity = reconcile_identity(mint, token_profile, market)
    assert identity["identity_status"] == "VERIFIED"
    report = {
        "mint": mint, "chain": "solana", "token_identity": identity,
        "assessment": {"narrative_status": "UNVERIFIED"},
    }

    requested = []

    class FakeJobs:
        def latest(self, supplied):
            requested.append(("C02_GET", supplied))
            return report if supplied == mint else None

    class FakeState:
        cluster_jobs = FakeJobs()

        def follow_opportunities(self):
            requested.append(("F01_GET", None))
            # The real handler delegates to actual F01 policy-created view.
            return follow

    class NativeControl(NativeControlHandler):
        state = FakeState()

    with serve_once(NativeControl) as ctrl, serve_once(
            f02_handler(f02_service)) as f02:
        join = JointReadOnly(control_port=ctrl.server_port,
                             f02_port=f02.server_port)
        with serve_once(make_handler(join)) as bridge:
            conn = HTTPConnection("127.0.0.1", bridge.server_port, timeout=4)
            conn.request("GET", "/api/research/alignment?mint=" + mint)
            resp = conn.getresponse()
            actual = json.loads(resp.read())
            assert resp.status == 200
            assert actual["status"] == "EXISTING_ARCHIVED_SOURCES_ONLY"
            assert actual["alignment"]["f01"]["status"] == "F01_ELIGIBLE"
            assert actual["alignment"]["c02"]["status"] == (
                "CA_EXACT_MINT_IDENTITY_VERIFIED")
            assert actual["alignment"]["f02"]["observed_quantity"] == (
                "123.000000")
            assert actual["combined_trade_permission"] is False

            conn.request("GET", "/api/research/alignment?mint=" + zero)
            resp = conn.getresponse()
            empty_ca = json.loads(resp.read())
            assert resp.status == 200
            assert empty_ca["status"] == "CA_NOT_QUERIED"
            assert empty_ca["alignment"]["f01"]["status"] == "F01_NOT_ELIGIBLE"
            assert empty_ca["alignment"]["c02"]["status"] == "CA_NOT_QUERIED"
            assert empty_ca["alignment"]["f02"]["observed_quantity"] == "0.000000"
            assert empty_ca["alignment"]["f02"]["state"] == "OPEN_ACCOUNT_ZERO"
            assert empty_ca["combined_trade_permission"] is False
            conn.close()

    assert requested == [
        ("F01_GET", None), ("C02_GET", mint),
        ("F01_GET", None), ("C02_GET", zero),
    ]
    assert Path(session["sidecar"]).read_bytes() == before
    assert len(rpc_calls) == 2
