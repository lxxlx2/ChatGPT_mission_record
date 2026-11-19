#!/usr/bin/env python3
"""BSC P4-B: pre-frozen historical market/wallet capital evidence; no entry signals."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "freeze": ("bsc-meme-address-model-v1-p4b-2026-fourmarket-fivewallet-precommit-2026-10-17.json",
               "b717dc49343d8050978305defe8061c05ee6fa54"),
    "readback": ("bsc-meme-address-model-v1-p4b-2026-fourmarket-fivewallet-rpc-readback-2026-10-17.json",
                 "5d55314fe88c7ab74d051b41074d6811813300b4"),
    "market": ("bsc-meme-address-model-v1-p4b-19ca-unified-early-market-buy-evidence-2026-10-14.json",
               "c42ad01e896f30262f89f7852f927fc84fb3ea18"),
    "grid": ("bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json",
             "f88ed9abfcb0f321ec31e98a029303aca48a8623"),
}
LABELS = {
    "DDAC": "0xddac928a240bdace3994c2cc0783d4e29a002127",
    "239E": "0x239e74bfbd02d71cdc70fecc2d505dc13acfb337",
    "2ADF": "0x2adf961b40951736bcff3b36b7fb1cd5775475ba",
    "A83B": "0xa83b73f5644cde337b61da79589f10ea15548811",
    "877AF": "0x877af245c61289b24f0c619a4346cdbc68f1aaac",
}
QUOTE = {
    "牛来": "0x205812cdbed920aff76c6580abd681a46d11efc7",
    "MARSCOIN": "0xbe9d156892e55e7154bcd3cb0fea677f9d3103e1",
}

def require(ok, code):
    if not ok:
        raise ValueError("P4B_2026_CAPITAL_" + code)

def load(root=ROOT):
    docs = {}
    for key, (file, pin) in SOURCES.items():
        raw = (root / file).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(actual == pin, "SOURCE_DRIFT_" + key)
        docs[key] = json.loads(raw)
    return docs

def build(docs):
    freeze, observed, market, grid = (docs[k] for k in ("freeze", "readback", "market", "grid"))
    require(observed["precommit_sha"] == SOURCES["freeze"][1] and
            observed["precommit_path"].endswith(SOURCES["freeze"][0]),
            "RESULT_BEFORE_PREFREEZE")
    require(freeze["approved_baseline"] == "375bd09f2bf893c18d23c03c2d158410fe6aa17d",
            "APPROVED_BASELINE")
    require(freeze["sample_role"] == "ALREADY_EXPOSED_RESEARCH_COHORT_NOT_UNTOUCHED_HOLDOUT",
            "HOLDOUT_MISLABEL")
    require(len(freeze["cases"]) == 4 and
            freeze["wallet_labels"] == list(LABELS) and
            len(observed["balance_cases"]) == 5 and
            len({x["token"] for x in freeze["cases"]}) == 4,
            "FROZEN_COHORT")
    markets = {x["token"]: x for x in market["rows"]}
    wallets = {w["wallet"].lower() for w in grid["wallets"]}
    require(len(wallets) == 23 and len(grid["markets"]) == 19 and
            grid["summary"]["implicit_wallet_CA_cells"] == 437 and
            len(market["rows"]) == 19 and len({m["exact_CA"] for m in market["rows"]}) == 19,
            "ORIGINAL_23x19_DENOMINATOR")
    require(set(LABELS.values()).issubset(wallets), "FROZEN_WALLET_IDENTITY")
    require([c["token"] for c in freeze["cases"]] ==
            ["龙虾", "牛来", "MARSCOIN", "我踏马来了"], "MARKET_ORDER")
    for m in freeze["cases"]:
        old = markets[m["token"]]
        require(old["exact_CA"] == m["ca"] and
                old["actual_global_observer_market_U"] == "UNRESOLVED" and
                old["following_at_1_5_15min"] == "UNRESOLVED",
                "EXACT_CA_OR_PREMATURE_U")
        if m["token"] == "我踏马来了":
            require(not m["wallet_labels"] and
                    m["original_signed_buy_block"] is None and
                    m["post_witness_block"] is None and
                    m["market_only_liquidity_reference_block"] ==
                    old["first_scoped_Pancake_positive_liquidity_block"] + 1 and
                    old["selected_early_buy_original_tx"] is None,
                    "MARKET_ONLY_AS_FAKE_SIGNED_SIGNAL")
        else:
            require(m["original_signed_buy_block"] == old["selected_early_buy_block"] and
                    m["post_witness_block"] == m["original_signed_buy_block"] + 1,
                    "POST_SIGNED_SIGNAL_BLOCK")
            if m["token"] == "龙虾":
                require(old["selected_early_buy_signer"] == LABELS["DDAC"],
                        "DRAGON_SIGNED_SOURCE")
            else:
                require(old["selected_signer_is_in_original_23"] is False and
                        old["observed_early_purchase_quote_CA"] == QUOTE[m["token"]],
                        "FLAP_QUOTE_SOURCE")
    valid_cases = {("龙虾", "DDAC"), ("龙虾", "239E"), ("牛来", "2ADF"),
                   ("牛来", "A83B"), ("MARSCOIN", "877AF")}
    rows = []
    for c in observed["balance_cases"]:
        label, token = c["label"], c["token"]
        require((token, label) in valid_cases and c["wallet"].lower() == LABELS[label],
                "ORIGINAL_CASE_WALLET")
        frozen = next(m for m in freeze["cases"] if m["token"] == token)
        require(label in frozen["wallet_labels"] and c["N"] == frozen["original_signed_buy_block"],
                "WITNESS_BLOCK_ATTRIBUTION")
        def parse_hex(s):
            require(isinstance(s, str) and s.startswith("0x") and len(s) > 2,
                    "RAW_HEX_REQUIRED")
            try:
                return int(s, 16)
            except ValueError as exc:
                raise ValueError("P4B_2026_CAPITAL_INVALID_HEX") from exc
        native_n = parse_hex(c["amount_at_N_hex"])
        native_next = parse_hex(c["amount_at_Nplus1_hex"])
        require(native_n == native_next and native_n >= 0, "N_TO_NPLUS1_SOURCE_CHANGE")
        if token in QUOTE:
            require(c.get("quote_ca") == QUOTE[token] and
                    parse_hex(c["quote_balance_Nplus1_raw_hex"]) >= 0,
                    "QUOTE_ASSET_OR_BALANCE")
        else:
            require("quote_ca" not in c and "quote_balance_Nplus1_raw_hex" not in c,
                    "NATIVE_QUOTE_FAKED_ERC20")
        rows.append({
            "wallet_label": label, "wallet": c["wallet"], "token": token,
            "witness_block_N": c["N"], "post_witness_observer_test_block_Nplus1": c["N"] + 1,
            "native_at_N_wei": str(native_n),
            "native_at_Nplus1_wei": str(native_next),
            "native_change_over_selected_two_block_ends_wei": str(native_next - native_n),
            "quote_token_ca": c.get("quote_ca"),
            "quote_at_Nplus1_raw": (str(parse_hex(c["quote_balance_Nplus1_raw_hex"]))
                                      if token in QUOTE else None),
            "capital_status": "HISTORICAL_BLOCK_END_BALANCE_ONLY_NOT_EXECUTABLE_CAPITAL",
            "publicly_observable_U": "UNRESOLVED",
            "actual_follower_fill": "UNRESOLVED",
        })
    require(len({(c["token"], c["wallet_label"]) for c in rows}) == 5 and
            {(c["token"], c["wallet_label"]) for c in rows} == valid_cases,
            "CASE_MISSING_OR_DUPLICATED")
    scans = observed["marscoin_sell_checks"]
    require([x["block"] for x in scans] == [112441395,112441396,112441397] and
            scans[0]["response_status"] == "COMPLETE_JSON" and
            scans[0]["total_events"] == 8 and scans[0]["exact_CA_events"] == 0 and
            len(set(scans[0]["non_target_txhashes"])) == 8 and
            all(x["raw_response_archived_in_git"] is False for x in scans) and
            all(x["response_status"] == "TRUNCATED_NON_JSON_8098_CHARS" and
                x["exact_CA_events"] is None for x in scans[1:]),
            "TRUNCATION_NOT_ALLOWED_AS_NEGATIVE_SELL")
    require(observed["gates"] == {"PUBLIC_U":"UNRESOLVED","P5":"BLOCKED","PRODUCTION":"NO_GO"},
            "GATE_PROMOTION")
    return {"schema":"BSC_P4B_2026_MARKET_OBSERVER_CAPITAL_READINESS_REPLAY",
            "source_pins": {k:v[1] for k,v in SOURCES.items()},
            "summary":{"market_CAs":4,"selected_original_wallet_cases":5,
                       "frozen_wallet_CA_universe":437,
                       "native_balance_readback_pairs":5,"ERC20_quote_balance_probes":3,
                       "marscoin_exact_CA_no_sell_proven_blocks":[112441395],
                       "marscoin_unresolved_truncated_blocks":[112441396,112441397],
                       "qualified_public_executable_U":0,"qualified_follower_returns":0,
                       "P4_B":"PARTIAL","P5":"BLOCKED","production":"NO_GO"},
            "cases": rows}

if __name__ == "__main__":
    print(json.dumps(build(load()), ensure_ascii=False, indent=2))
