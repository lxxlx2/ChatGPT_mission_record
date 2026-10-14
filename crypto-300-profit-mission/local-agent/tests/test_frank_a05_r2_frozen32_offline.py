"""A05-R2 tests: the historical frozen 32 and complete original-wire evidence."""
import json

import pytest

from mission_agent.mission_control.wallet_chain_capture import (
    SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM,
)
from mission_agent.mission_control.wallet_full_rpc_evidence import (
    collect_owner_full_receipts,
)
from scripts.frank_reconcile_frozen32_offline import (
    ROSTER, ROSTER_GIT_BLOB, _git_blob, load_frozen_roster, main, reconcile,
)
from test_frank_a04_a05_chain_capture import entry, pk


WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"


def _wire(rpc_id, slot, records):
    return json.dumps({"jsonrpc": "2.0", "id": rpc_id,
                       "result": {"context": {"slot": slot}, "value": records}}
                      ).encode("utf-8")


@pytest.fixture
def frozen():
    return load_frozen_roster(ROSTER, WALLET)


@pytest.fixture
def full_bundle(tmp_path, frozen):
    first, second = [r["mint"] for r in frozen["records"][:2]]
    spl = _wire(1, 456900000, [
        entry(WALLET, first, pk(90), SPL_TOKEN_PROGRAM, amount="123000000"),
        entry(WALLET, first, pk(91), SPL_TOKEN_PROGRAM, amount="0"),
    ])
    token2022 = _wire(2, 456900001, [
        entry(WALLET, second, pk(92), TOKEN_2022_PROGRAM, amount="0"),
    ])
    captured = collect_owner_full_receipts(
        wallet=WALLET, evidence_root=tmp_path / "source",
        read_raw=lambda method, params, ident: spl if ident == 1 else token2022,
        observed_at_utc="2026-10-14T16:00:00+00:00",
    )
    assert captured["manifest"]["complete"]
    return captured


def test_historical_roster_is_provenance_pinned_and_exact_32(frozen):
    assert _git_blob(ROSTER.read_bytes()) == ROSTER_GIT_BLOB
    assert len(frozen["records"]) == 32
    assert len({r["mint"] for r in frozen["records"]}) == 32
    assert frozen["summary"] == {"checked": 32, "nonzero": 10, "zero": 22}


def test_roster_tamper_or_identity_conflict_is_rejected(tmp_path):
    mutated = ROSTER.read_bytes().replace(b'"checked": 32', b'"checked": 31')
    target = tmp_path / "altered.json"
    target.write_bytes(mutated)
    with pytest.raises(ValueError, match="FROZEN_32_MINT_ROSTER_BLOB_MISMATCH"):
        load_frozen_roster(target, WALLET)
    with pytest.raises(ValueError, match="FROZEN_32_MINT_ROSTER_INVALID"):
        load_frozen_roster(ROSTER, pk(99))


def test_full_source_filters_thousands_of_unrelated_mints_without_false_zero(
        frozen, full_bundle):
    report = reconcile(full_bundle["snapshot"], frozen)
    s = report["summary"]
    assert s["frozen_target_mints"] == 32
    assert s["whole_wallet_observed_token_accounts"] == 3
    assert s["whole_wallet_observed_unique_mints"] == 2
    assert s["targets_with_open_account"] == 2
    assert s["targets_with_positive_balance"] == 1
    assert s["targets_with_zero_open_account"] == 1
    assert s["targets_with_no_open_account_observed"] == 30
    assert s["targets_with_multiple_open_accounts"] == 1
    assert s["target_open_token_accounts"] == 3
    first = report["mints"][0]
    assert first["observed_raw_amount"] == "123000000"
    assert first["observed_token_account_count"] == 2
    assert first["historical_to_new_raw_delta"] == "123000000"
    absent = report["mints"][2]
    assert absent["observed_raw_amount"] is None
    assert absent["observed_quantity"] is None
    assert absent["current_status"] == "NO_OPEN_ACCOUNT_OBSERVED"
    assert report["history_complete"] is False
    assert report["verified_cost_or_pnl"] is False


def test_incomplete_source_and_wallet_mismatch_rejected(frozen, full_bundle):
    capture = full_bundle["snapshot"]
    for mutation in [
        {"both_programs_observed": False}, {"missing": [{"bad": True}]},
        {"wallet": pk(99)}, {"same_slot_atomic": True},
    ]:
        test = {**capture, **mutation}
        with pytest.raises(ValueError, match="DUAL_PROGRAM_VERIFIED_SOURCE_REQUIRED"):
            reconcile(test, frozen)


def test_reconciliation_requires_internally_consistent_whole_source(
        frozen, full_bundle):
    capture = full_bundle["snapshot"]
    for change in [
        {"account_count": 2}, {"mint_count_observed": 3},
        {"mints": capture["mints"] + [capture["mints"][0]]},
    ]:
        with pytest.raises(ValueError):
            reconcile({**capture, **change}, frozen)


def test_cli_real_offline_bundle_outputs_local_0600_and_no_network_or_sqlite(
        tmp_path, full_bundle, capsys, monkeypatch):
    from urllib import request
    monkeypatch.setattr(request, "urlopen", lambda *a, **k:
                        pytest.fail("offline must not call RPC"))
    report_file = tmp_path / "private" / "reconciled.json"
    result = main(["--bundle", full_bundle["bundle"], "--output", str(report_file)])
    assert result == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "FROZEN32_OFFLINE_ACCOUNT_RECONCILIATION_COMPLETED"
    assert out["summary"]["frozen_target_mints"] == 32
    assert out["network_invoked"] is False
    assert out["writes_production_sqlite"] is False
    assert report_file.stat().st_mode & 0o777 == 0o600
    assert report_file.parent.stat().st_mode & 0o777 == 0o700
    report = json.loads(report_file.read_text())
    assert len(report["mints"]) == 32
    assert not list(tmp_path.rglob("*.sqlite"))
    with pytest.raises(FileExistsError):
        main(["--bundle", full_bundle["bundle"], "--output", str(report_file)])


def test_partial_bundle_not_replayable_even_with_valid_frozen_roster(
        tmp_path, frozen):
    good = _wire(1, 456900005, [])
    broken = b'{"jsonrpc":"2.0","id":2,"result":'
    source = collect_owner_full_receipts(
        wallet=WALLET, evidence_root=tmp_path / "partial",
        read_raw=lambda m, p, ident: good if ident == 1 else broken,
    )
    assert source["manifest"]["complete"] is False
    with pytest.raises(ValueError, match="OWNER_SOURCE_NOT_FULLY_VERIFIED"):
        main(["--bundle", source["bundle"]])


def test_invalid_public_repo_output_rejected(full_bundle):
    from scripts.frank_reconcile_frozen32_offline import ROOT
    with pytest.raises(ValueError, match="OWNER_EVIDENCE_INSIDE_GIT_CHECKOUT_FORBIDDEN"):
        main(["--bundle", full_bundle["bundle"],
              "--output", str(ROOT / "should-not-save-private-wallet.json")])
