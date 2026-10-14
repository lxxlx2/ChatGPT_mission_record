#!/usr/bin/env python3
"""Verify original real Flap Portal TokenBought owners, quote assets, tax and scoped exits.

Two 2026 *market* witnesses are NOT an expansion of the precommitted 23 candidate
wallets; historical eth_call math is NOT an actual sell, and received tokens
alone are NOT signed owner PnL. All raw sources are pinned by Git blob SHA.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4b-2026-major3-first-txs-part2-2026-10-14.json","7e2e4f3cb779cd9511c2d5670e3a90f403616684"),("bsc-meme-address-model-v1-p4b-2026-major3-first-txs-part3-2026-10-14.json","5208fe6dbffdef6ed642697bcab1ff29e2bf1b9b"),("bsc-meme-address-model-v1-p4b-first10-erc20-pre-dex-part4-2026-10-14.json","ed68cd1ae0245132ec1eafa8d7803d12c802d685"),("bsc-meme-address-model-v1-p4b-first10-erc20-pre-dex-part5-2026-10-14.json","7607887812df4ef0219bac8aa069776451b9249a"),("bsc-meme-address-model-v1-p4b-flap-major2-topic-raw-part1-2026-10-14.json","b7bd1f907e94e2103b2c4e35c763ea18cf15b28e"),("bsc-meme-address-model-v1-p4b-flap-major2-topic-raw-part2-2026-10-14.json","1cd57c862cc373183dcd1df05853863268ce4586"),("bsc-meme-address-model-v1-p4b-flap-major2-quote-tax-part1-2026-10-14.json","302b4983f750c50957d84869d15dcc40ac2af8bd"),("bsc-meme-address-model-v1-p4b-flap-major2-quote-tax-part2-2026-10-14.json","70f93b2e8ac2be4e1cdb803b3510ae360cb54e77"),("bsc-meme-address-model-v1-p4b-flap-major2-quote-decimals-raw-2026-10-14.json","1dd5c89162a9a510d6bcf0f585293ee1efe0d40f"),("bsc-meme-address-model-v1-p4b-flap-major2-bidirectional-quotes-raw-2026-10-14.json","43fe6d36fbeeda43e07a2b65874c4292e5d91606"),("bsc-meme-address-model-v1-p4b-flap-major2-postbuy-sell-raw-2026-10-14.json","69e2147e4f689c21335a7bb84695269d84caca4e"),("bsc-meme-address-model-v1-p4b-marscoin-oneblock-sell-fallback-raw-2026-10-14.json","42fffee80171b4fa5d3c256167b022d2b34d6297"),("bsc-meme-address-model-v1-p4-p2p3-readiness-matrix-2026-10-13.json","3252e05c3ef1a4de14a5e10aed3e5ba80566154f"))
PORTAL="0xe2ce6ab80874fa9fa2aae65d277dd6b8e65c9de0"
CREATE_TOPIC="0x504e7f360b2e5fe33cbaaae4c593bc55305328341bf79009e43e0e3b7f699603"
BUY_TOPIC="0xa800a2038683844fac66747f771bfdfae862eb28b16bcfa387afa9fbacce8ff7"
PAIR=(("牛来","0xbeea1d618e533a387d941f58a7d4c9b7bd377777",100),
      ("MARSCOIN","0xfe189e97832da1573e4e4ff034f4ffc3a15c7777",300))

def require(ok,message):
    if not ok: raise ValueError(message)

def git_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load(root=ROOT):
    docs=[]
    for n,h in PINS:
        raw=(root/n).read_bytes()
        require(git_sha(raw)==h,"Git provenance drift: "+n)
        docs.append(json.loads(raw))
    return docs

def parse_words(log,count):
    h=log["data"]
    require(isinstance(h,str) and h.startswith("0x") and len(h)>=2+64*count,
            "Flap event ABI raw data truncated")
    return [int(h[2+64*i:2+64*(i+1)],16) for i in range(count)]

def addr(i):
    return "0x"+format(i,"040x")

def time(ts):
    return datetime.fromtimestamp(ts,tz=timezone.utc).isoformat().replace("+00:00","Z")

def one_event(part,name):
    rows=[x for x in part["rows"] if x["event"]==name and len(x["source_target_events"])==1]
    require(len(rows)==1 and rows[0]["rpc_complete"] is True,"original Flap "+name+" unresolved or ambiguous")
    e=rows[0]["source_target_events"][0]
    require(e["transactionHash"].lower()==rows[0]["tx"].lower()
            and int(e["blockNumber"],16)==rows[0]["block"]
            and e["address"].lower()==PORTAL
            and e["topics"][0]==(BUY_TOPIC if name=="TokenBought" else CREATE_TOPIC)
            and e.get("removed") is not True,
            "event hash/contract/topic not original selected")
    return e

def build(d):
    require(len(d)==13,"two major original sources or original roster missing")
    original,transfers,topic,config=d[:2],d[2:4],d[4:6],d[6:8]
    decimals=d[8]["rows"]
    math=d[9]["rows"]
    sells=d[10]["rows"]
    fallback=d[11]
    wallet_roster=d[12]
    require(wallet_roster["summary"]["wallets"]==23
            and len(wallet_roster["wallets"])==23
            and wallet_roster["summary"]["production"]=="NO_GO",
            "research wallet roster changed")
    known={w["wallet"].lower() for w in wallet_roster["wallets"]}
    require(fallback["schema"]=="BSC_P4B_MARSCOIN_ONEBLOCK_SELL_FALLBACK_RAW"
            and fallback["query_status"]=="COMPLETE"
            and not fallback["exact_CA_events"]
            and fallback["production"]=="NO_GO",
            "one-block original MARS sale source not complete")
    rows=[]
    for i,(token,CA,tax_rate) in enumerate(PAIR):
        src=original[i]["rows"]
        require(len(src)==2 and src[1]["selection"]["token"]==token
                and src[1]["selection"]["selected_role"]=="FIRST_DISTINCT_POST_MINT_TRANSFER_TX"
                and original[i]["production"]=="NO_GO", "first original tx source changed")
        signed=src[1]["transaction"]
        signer=signed["from"].lower()
        ev_buy=one_event(topic[i],"TokenBought")
        ev_create=one_event(topic[i],"TokenCreated")
        b=parse_words(ev_buy,7)
        c=parse_words(ev_create,7)
        require(addr(b[1])==addr(c[3])==CA
                and ev_buy["transactionHash"].lower()==signed["hash"].lower()
                and ev_create["transactionHash"].lower()==src[0]["transaction"]["hash"].lower()
                and int(ev_buy["blockNumber"],16)==int(signed["blockNumber"],16)
                and int(ev_create["blockNumber"],16)<int(ev_buy["blockNumber"],16)
                and src[1]["tx_status"]=="COMPLETE"
                and src[1]["receipt_status"]=="UNRESOLVED"
                and signer not in known,
                "selected original signer or source market altered")
        erc=next(x for x in transfers[i]["rows"] if x["token"]==token)
        hops=[x for x in erc["transfers"] if x["hash"].lower()==signed["hash"].lower()]
        buyer=addr(b[2])
        finals=[x for x in hops if x["to"].lower()==signer]
        require(len(finals)==1 and int(finals[0]["rawContract"]["value"],16)==b[3]
                and all(x["rawContract"]["address"].lower()==CA for x in hops)
                and any(x["from"].lower()==PORTAL for x in hops)
                and any(x["to"].lower()==buyer for x in hops),
                "exact original TokenBought amount not delivered to original EOA signer")
        quote=next(x for x in config[i]["rows"] if x["event"]=="TokenQuoteSet")
        tax=next(x for x in config[i]["rows"] if x["event"]=="FlapTokenAsymmetricTaxSet")
        require(len(quote["original_creation_tx_events"])==1 and len(tax["original_creation_tx_events"])==1
                and quote["query_complete"] and tax["query_complete"], "Flap quote and fee creation config missing")
        q=parse_words(quote["original_creation_tx_events"][0],2)
        t=parse_words(tax["original_creation_tx_events"][0],3)
        quoteCA=addr(q[1])
        require(addr(q[0])==addr(t[0])==CA
                and t[1]==t[2]==tax_rate and quoteCA!="0x"+"0"*40,
                "wrong onchain buy/sell tax or quote CA")
        meta=next(x for x in decimals if x["token"]==token)
        quote_math=next(x for x in math if x["token"]==token)
        sell=next(x for x in sells if x["token"]==token)
        require(meta["quote_CA"]==quoteCA
                and int(meta["decimals_at_buy_raw"],16)==18
                and int(meta["decimals_creation_raw"],16)==18
                and quote_math["quote_CA"]==sell["quote_CA"]==quoteCA
                and quote_math["buy_read"]["status"]=="COMPLETE_QUOTE_ONLY"
                and quote_math["fixed_quote_in_raw"]=="10000000000000000"
                and int(quote_math["buy_read"]["raw"],16)>0
                and sell["actual_bought_token_raw"]==str(b[3])
                and sell["postbuy_quote_status"]=="COMPLETE_QUOTE_ONLY"
                and int(sell["postbuy_quoteread_raw"],16)>0
                and sell["buy_block"]==int(ev_buy["blockNumber"],16),
                "historical quote path or block amount not corroborated")
        if i==0:
            require(sell["sell_logs_full_window_status"]=="COMPLETE"
                    and sell["sell_window_end"]-sell["sell_window_start"]==9
                    and len(sell["exact_CA_sell_events"])==0,
                    "Niulai 10-block sell evidence not complete")
            sold_count=len(sell["exact_CA_sell_events"])
            salescope="COMPLETE_FIRST10_BLOCKS"
        else:
            require(sell["sell_logs_full_window_status"]=="UNRESOLVED"
                    and len(fallback["exact_CA_events"])==0, "MARS 10-block must stay truncated")
            sold_count=len(fallback["exact_CA_events"])
            salescope="COMPLETE_FIRST_BLOCK_ONLY_TEN_BLOCK_QUERY_TRUNCATED"
        rows.append({
            "token":token,"exact_CA":CA,
            "platform":"FLAP_PORTAL_BNB_MAINNET","portal":PORTAL,
            "creation_block":int(ev_create["blockNumber"],16),
            "creation_UTC":time(int(ev_create["blockTimestamp"],16)),
            "first_sampled_buy_block":int(ev_buy["blockNumber"],16),
            "first_sampled_buy_UTC":time(int(ev_buy["blockTimestamp"],16)),
            "blocks_since_creation":int(ev_buy["blockNumber"],16)-int(ev_create["blockNumber"],16),
            "original_EOA_signer":signer,"signed_tx_hash":signed["hash"],
            "signed_tx_to":signed["to"],
            "signed_tx_native_value_wei":str(int(signed["value"],16)),
            "portal_TokenBought_intermediate_buyer":buyer,
            "final_ERC20_recipient":signer,
            "intermediate_hops":[{
                "from":x["from"],"to":x["to"],
                "raw_amount":str(int(x["rawContract"]["value"],16))
            } for x in hops],
            "received_target_raw":str(b[3]),
            "portal_event_quote_spent_raw":str(b[4]),
            "portal_event_fee_raw":str(b[5]),
            "actual_quote_CA":quoteCA,
            "historical_quote_decimals":18,
            "quote_symbol_current_metadata":meta["metadata_current"]["symbol"],
            "quote_symbol_is_not_assumed_USD":True,
            "buy_tax_bps":t[1],"sell_tax_bps":t[2],
            "original_first_purchase_event_match":"CONFIRMED",
            "net_fee_plus_quote_from_wallet":"UNRESOLVED",
            "causal_profit":"UNRESOLVED",
            "full_transaction_receipt":"UNRESOLVED_TRUNCATED",
            "pre_buy_fixed_001_quote_input_raw":quote_math["fixed_quote_in_raw"],
            "pre_buy_quoted_target_raw":quote_math["buy_read"]["raw"],
            "pre_buy_quoted_status":quote_math["buy_read"]["status"],
            "post_buy_full_original_inventory_reverse_quote_raw":sell["postbuy_quoteread_raw"],
            "post_buy_reverse_quote_status":sell["postbuy_quote_status"],
            "observed_postbuy_sells_in_scope":sold_count,
            "observed_postbuy_sell_scope":salescope,
            "buyer_in_frozen_23":"NO",
            "first_global_U":"UNRESOLVED",
            "follower_entry_1_5_15min":"UNRESOLVED",
            "production":"NO_GO"
        })
    return {
      "schema":"BSC_P4B_FLAP_2026_TWO_REAL_EARLY_PURCHASE_QUOTE_AND_TAX_ECONOMICS",
      "scope":"Source-pinned Niulai and Marscoin original Portal TokenCreated and TokenBought, original externally signed tx, exact original ERC20 routed receipt closure to signer, tax/quote config and actual historical 18-decimal quote contract. Quote math isn't a settled round trip. Both signers outside precommitted 23 candidate wallets; only positive 2026 market opportunity existence evidence, not 23-wallet alpha.",
      "source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
      "summary":{
         "tokens":2,"source_original_signed_purchases":2,
         "signer_recipient_inventory_matches":2,
         "actual_non_native_erc20_quote_CAs":2,
         "creation_asymmetric_tax_events":2,
         "postbuy_reverse_math_quote_returns":2,
         "proven_historic_successful_sells":0,"closed_PnL":0,
         "qualified_first_market_U":0,"production":"NO_GO"
      },"rows":rows
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
