"""F02-R3 research-only private source attestation, no chain/network/prod write."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from mission_agent.mission_control.wallet_chain_capture import SPL_TOKEN_PROGRAM
from scripts import frank_f02_r3_offline_attestation as audit
from scripts.frank_f02_manual_refresh import refresh_session
from test_frank_f02_manual_refresh import reader, WALLET
from test_frank_a04_a05_chain_capture import entry, pk
from scripts.frank_reconcile_frozen32_offline import ROSTER, load_frozen_roster


def capture(tmp_path, read=None):
    read_fn, calls = reader() if read is None else (read, [])
    summary, _ = refresh_session(
        session_root=tmp_path / "manual-sessions", read_raw=read_fn)
    return summary, calls


def test_private_real_wire_sidecar_crosscheck_offline_no_mutation(tmp_path):
    summary, calls = capture(tmp_path)
    assert len(calls) == 2
    session = Path(summary["session_directory"])
    before = Path(summary["sidecar"]).read_bytes()
    root = tmp_path / "manual-sessions"
    selected = audit.find_session(root, summary["capture_sha256"])
    assert selected == session
    report = audit.attest(selected, summary["capture_sha256"],
                          now_utc=datetime.now(timezone.utc) + timedelta(seconds=360))
    assert report["status"] == "F02_R3_PRIVATE_ORIGINAL_WIRE_READONLY_REPLAY_PASS"
    assert report["frozen_targets"] == 32
    assert report["frozen_positive"] == 1
    assert report["frozen_zero"] == 1
    assert report["frozen_no_open_account"] == 30
    assert report["frozen_accounts_total"] == 2
    assert report["frozen_multi_account_mints"] == 0
    assert report["frozen_max_accounts_per_mint"] == 1
    assert report["whole_wallet_observed_token_accounts"] == 2
    assert report["whole_wallet_observed_unique_mints"] == 2
    assert report["as_of_now_readiness"] == "STALE_ARCHIVED_SOURCE"
    assert report["archived_all32_mint_and_individual_accounts_compared"] is True
    assert report["network_invoked"] is False
    assert report["writes_production_sqlite"] is False
    assert "token_accounts" not in report
    assert "wallet" not in report
    assert Path(summary["sidecar"]).read_bytes() == before


def test_two_token_accounts_for_same_mint_are_compared_individually(tmp_path):
    underlying, calls = reader()
    target = load_frozen_roster(ROSTER, WALLET)["records"][0]["mint"]

    def with_two_accounts(method, params, ident):
        response = json.loads(underlying(method, params, ident))
        if ident == 1:
            response["result"]["value"].append(entry(
                WALLET, target, pk(95), SPL_TOKEN_PROGRAM, amount="1000000"))
        return json.dumps(response).encode()

    summary, _ = capture(tmp_path, read=with_two_accounts)
    report = audit.attest(Path(summary["session_directory"]),
                          summary["capture_sha256"])
    assert report["frozen_positive"] == 1
    assert report["frozen_accounts_total"] == 3
    assert report["frozen_multi_account_mints"] == 1
    assert report["frozen_max_accounts_per_mint"] == 2
    assert report["whole_wallet_observed_token_accounts"] == 3
    assert report["whole_wallet_observed_unique_mints"] == 2
    assert len(calls) == 2


def test_tampered_original_wire_and_unmatched_sha_fail_closed(tmp_path):
    summary, _ = capture(tmp_path)
    session = Path(summary["session_directory"])
    with pytest.raises(ValueError, match="UNIQUE_SESSION"):
        audit.find_session(tmp_path / "manual-sessions", "f" * 64)
    with pytest.raises(ValueError, match="SHA_MISMATCH"):
        audit.attest(session, "f" * 64)
    wire_files = sorted((session / "wire").glob("owner-*/*.json"))
    wire = next(p for p in wire_files if p.name != "manifest.json")
    wire.write_bytes(wire.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA_MISMATCH"):
        audit.attest(session, summary["capture_sha256"])


def test_cli_emits_private_safe_aggregate_and_missing_raises(tmp_path, capsys):
    summary, _ = capture(tmp_path)
    code = audit.main(["--capture-sha256", summary["capture_sha256"],
                       "--session-root", str(tmp_path / "manual-sessions")])
    assert code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["frozen_targets"] == 32
    assert "session_directory" not in result
    assert "positions.sqlite" not in str(result)
    assert WALLET not in str(result)
    assert audit.main(["--capture-sha256", "z" * 64,
                       "--session-root", str(tmp_path / "manual-sessions")]) == 1
