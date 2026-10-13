"""A03 to A05 local user workflow replay and manual CLI plan guard."""
import json
from pathlib import Path
import runpy

from mission_agent.mission_control.person_registry import PersonRegistry
from mission_agent.mission_control.research_wallet_facts import PersonResearchReader
from mission_agent.mission_control.wallet_capture_provider import CapturedWalletFactsProvider
from mission_agent.mission_control.wallet_chain_capture import (
    SPL_TOKEN_PROGRAM, capture_owner,
)
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def pub(seed):
    number = int.from_bytes(bytes([seed]) * 32, "big")
    digits = ""
    while number:
        number, remain = divmod(number, 58)
        digits = ALPHABET[remain] + digits
    return digits


W1, W2, MINT, ATA1, ATA2 = [pub(i) for i in range(10, 15)]


def person(pid, wallet):
    return {"person_id": pid, "display_name": pid,
            "enabled": pid == "frank", "research_enabled": True,
            "wallets": [{"chain": "solana", "address": wallet, "role": "PRIMARY",
                         "valid_from_slot": 100}]}


def fake_account(wallet, ata, program, raw):
    return {"pubkey": ata, "account": {"owner": program,
        "data": {"parsed": {"type": "account", "info": {
            "owner": wallet, "mint": MINT, "state": "initialized",
            "tokenAmount": {"amount": raw, "decimals": 6},
        }}}}}


def fake_rpc(wallet, first_raw, second_raw):
    def query(method, params):
        assert method == "getTokenAccountsByOwner"
        program = params[1]["programId"]
        first = program == SPL_TOKEN_PROGRAM
        slot = 200 if first else 201
        key = ATA1 if first else ATA2
        raw = first_raw if first else second_raw
        return {"result": {"context": {"slot": slot},
                           "value": [fake_account(wallet, key, program, raw)]}}
    return query


def test_realistic_a03_a05_sidecar_multi_ata_roundtrip_has_evidence_not_pnl(tmp_path):
    reg = PersonRegistry.from_mapping({"schema_version": 2,
                                       "persons": [person("frank", W1),
                                                   person("research_b", W2)]})
    store = WalletEvidenceStore(tmp_path / "wallet-research.sqlite")
    try:
        capture_a = capture_owner(W1, fake_rpc(W1, "1000000", "2000000"))
        capture_b = capture_owner(W2, fake_rpc(W2, "9000000", "1000000"))
        assert store.capture_wallet(capture_a)
        assert store.capture_wallet(capture_b)
        reader = PersonResearchReader(reg, CapturedWalletFactsProvider(store))
        frank = reader.mint_observations(person_id="frank", mint=MINT,
                                         as_of_slot=201)
        other = reader.mint_observations(person_id="research_b", mint=MINT,
                                         as_of_slot=201)
        assert frank["wallets"][0]["inventory"]["balance"]["quantity"] == "3"
        assert other["wallets"][0]["inventory"]["balance"]["quantity"] == "10"
        assert len(frank["wallets"][0]["inventory"]["balance"]["token_accounts"]) == 2
        assert frank["wallets"][0]["inventory"]["balance"]["slot_min"] == 200
        assert frank["wallets"][0]["inventory"]["balance"]["slot_max"] == 201
        assert frank["wallets"][0]["inventory"]["balance"]["both_token_programs_observed"]
        assert "CHAIN_SNAPSHOT_NON_ATOMIC" in frank["wallets"][0]["inventory"]["missing"]
        assert not frank["portfolio_verified"] and not frank["chain_complete"]
        assert frank["person_balance"] is frank["person_pnl_usd"] is None
        assert not other["signal_allowed"] and not other["delivery_allowed"]
        before = reader.mint_observations(person_id="frank", mint=MINT,
                                          as_of_slot=199)
        assert before["wallets"][0]["inventory"]["balance"] is None
        assert before["wallets"][0]["inventory"]["status"] == "NOT_CAPTURED"
    finally:
        store.close()


def test_optional_manual_cli_defaults_to_plan_only_and_no_sidecar(tmp_path, capsys):
    root = Path(__file__).resolve().parents[1]
    script = runpy.run_path(str(root / "scripts/frank_capture_owner_readonly.py"))
    reg = tmp_path / "registry.json"
    reg.write_text(json.dumps({"schema_version": 2, "persons": [person("frank", W1)]}))
    sidecar = tmp_path / "readonly-sidecar.sqlite"
    assert script["main"](["--registry", str(reg),
                           "--sidecar", str(sidecar)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["status"] == "PLAN_ONLY"
    assert status["network_invoked"] is False
    assert status["writes_production_sqlite"] is False
    assert not sidecar.exists()
