"""Frank normalized transfer records are readable without export of raw RPC secrets."""
import json
import sqlite3
from pathlib import Path

import pytest
from mission_agent.mission_control.wallet_transfers import export_signature_evidence

MINT = "J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump"
FRANK = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"


def test_passive_transfer_preserves_public_evidence_only(tmp_path):
    dbpath = tmp_path / "forward.sqlite"
    db = sqlite3.connect(dbpath)
    db.execute("CREATE TABLE signatures(wallet TEXT,person_id TEXT,signature TEXT,block_time INTEGER,body TEXT)")
    payload = {
        "classification": "PASSIVE_TRANSFER",
        "classification_reason": "NOT_WALLET_SIGNED",
        "api_key": "DO_NOT_EXPORT",
        "evidence": {
            "slot": 454705300,
            "mechanical_classification": "PASSIVE_RECEIPT_LIKE",
            "wallet_is_signer": False, "wallet_is_fee_payer": False,
            "raw_transaction_sha256": "a"*64, "source_rpc": "PRIVATE_API_URL",
            "wallet_token_transfer_flows": [{
                "mint": MINT, "direction": "IN", "raw_amount": "2846838050235",
                "decimals": 6, "source": "source-ata", "destination": "frank-ata",
                "provider_auth": "DO_NOT_EXPORT",
            }],
            "token_balance_deltas": [{
                "mint": MINT, "owner": FRANK, "wallet_owned": True,
                "pre_amount": "0", "post_amount": "2846838050235",
                "delta": "2846838050235", "decimals": 6,
            }, {"mint": MINT, "owner": "other", "wallet_owned": False, "delta": "-2846838050235"}],
        },
    }
    db.execute("INSERT INTO signatures VALUES (?,?,?,?,?)",
               (FRANK, "frank", "signature-1", 1791505760, json.dumps(payload)))
    db.commit()
    report = export_signature_evidence(dbpath)
    assert report["record_count"] == 1
    assert report["local_classifications"]["PASSIVE_TRANSFER"] == 1
    x = report["records"][0]
    assert x["wallet_is_signer"] is False
    assert x["transfer_flows"][0]["raw_amount"] == "2846838050235"
    assert x["counterparty_attribution_status"] == "PARSED_TOKEN_ACCOUNT_FLOW"
    assert report["all_counterparties_verified"] is True
    assert len(x["wallet_owned_token_deltas"]) == 1
    assert x["wallet_owned_token_deltas"][0]["owner"] == FRANK
    assert "DO_NOT_EXPORT" not in json.dumps(report)
    assert "PRIVATE_API_URL" not in json.dumps(report)
    assert report["chain_history_complete"] is False
    assert report["pnl_verified"] is False
    assert db.execute("SELECT COUNT(*) FROM signatures").fetchone()[0] == 1
    db.close()


def test_duplicate_signatures_fail_closed(tmp_path):
    p=tmp_path/"forward.sqlite"
    db=sqlite3.connect(p)
    db.execute("CREATE TABLE signatures(wallet TEXT,person_id TEXT,signature TEXT,block_time INTEGER,body TEXT)")
    for i in range(2):
        db.execute("INSERT INTO signatures VALUES (?,?,?,?,?)",(FRANK,"frank","same",1000,"{}"))
    db.commit()
    with pytest.raises(ValueError,match="DUPLICATE"):
        export_signature_evidence(p)
    db.close()


def test_missing_db_is_not_created(tmp_path):
    p=tmp_path/"not-there.sqlite"
    with pytest.raises((OSError,sqlite3.Error)):
        export_signature_evidence(p)
    assert not p.exists()


def test_passive_balance_delta_without_parsed_source_is_explicitly_unattributed(tmp_path):
    p = tmp_path / "forward.sqlite"
    db = sqlite3.connect(p)
    db.execute("CREATE TABLE signatures(wallet TEXT,person_id TEXT,signature TEXT,block_time INTEGER,body TEXT)")
    body = {
        "classification": "PASSIVE_TRANSFER",
        "evidence": {
            "wallet_is_signer": False,
            "wallet_token_transfer_flows": [],
            "token_balance_deltas": [{
                "mint": MINT, "owner": FRANK, "wallet_owned": True,
                "delta": "2846838050235", "pre_amount": "0",
                "post_amount": "2846838050235", "decimals": 6
            }],
        },
    }
    db.execute("INSERT INTO signatures VALUES(?,?,?,?,?)",
               (FRANK, "frank", "sig-passive-1", 1791505760, json.dumps(body)))
    db.commit()
    actual = export_signature_evidence(p)
    assert actual["record_count"] == 1
    assert actual["source_attribution_coverage"]["passive_nonzero_delta_without_parsed_counterparty"] == 1
    assert actual["source_attribution_coverage"]["signature_rows_with_parsed_counterparty_flows"] == 0
    assert actual["records"][0]["counterparty_attribution_status"] == (
        "BALANCE_DELTA_ONLY_COUNTERPARTY_UNRESOLVED")
    assert actual["all_counterparties_verified"] is False
    assert actual["records"][0]["transfer_flows"] == []
    db.close()
