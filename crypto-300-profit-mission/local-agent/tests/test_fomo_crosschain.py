"""No-network regression tests for FOMO cross-chain evidence attribution."""
import json
import runpy
from pathlib import Path

import pytest

from mission_agent.meme import fomo_crosschain as fc


def b58encode(value):
    number=int.from_bytes(value,"big")
    text=""
    while number:
        number,remainder=divmod(number,58)
        text=fc._BASE58[remainder]+text
    return "1"*(len(value)-len(value.lstrip(b"\0")))+text


def topic(wallet):
    return "0x"+"0"*24+wallet.lower().removeprefix("0x")


def data_words(*words):
    return "0x"+"".join(format(x,"064x") if isinstance(x,int)
                          else x.lower().removeprefix("0x").rjust(64,"0") for x in words)


def log(index, address, topics, data="0x"):
    return {"logIndex":hex(index),"blockNumber":"0x10","address":address,
            "topics":topics,"data":data,"transactionHash":"0x"+"9"*64}


def balances(wallet, before, after, mint=fc.USDC):
    a={"accountIndex":2,"mint":mint,"owner":wallet,
       "uiTokenAmount":{"amount":str(before),"decimals":6}}
    b={"accountIndex":2,"mint":mint,"owner":wallet,
       "uiTokenAmount":{"amount":str(after),"decimals":6}}
    return [a],[b]


def sol_tx(wallet, *, signed=True, cosigned=True, solver=False, before=5_000_000,
           after=0, instructions=()):
    pre,post=balances(wallet,before,after)
    return {"slot":1212,"blockTime":1791472000,
            "transaction":{"message":{"accountKeys":[
                {"pubkey":wallet,"signer":signed},
                {"pubkey":fc.FOMO_COSIGNER,"signer":cosigned},
                {"pubkey":fc.USDC,"signer":False},
                {"pubkey":fc.SOL_RELAY_SOLVER,"signer":solver},
            ],"instructions":list(instructions)}},
            "meta":{"err":None,"preTokenBalances":pre,"postTokenBalances":post,
                    "innerInstructions":[]}}


def test_solana_relay_cash_payment_requires_wallet_signature_and_exact_instruction():
    oid="0x"+"1"*64
    payload=fc.DEPOSIT_DISCRIMINATOR+(5_000_000).to_bytes(8,"little")+bytes.fromhex(oid[2:])
    ix={"programId":fc.SOL_RELAY_DEPOSIT,"data":b58encode(payload)}
    rows=fc.solana_events("sig1",sol_tx(fc.SOL_CASH_WALLET,instructions=[ix]),fc.SOL_CASH_WALLET)
    assert len(rows)==1
    assert rows[0]["kind"]=="RELAY_PAY" and rows[0]["order_id"]==oid
    assert rows[0]["amount_raw"]=="5000000"
    assert rows[0]["signal_eligible"] is False
    unsigned=sol_tx(fc.SOL_CASH_WALLET,signed=False,instructions=[ix])
    assert fc.solana_events("sig2",unsigned,fc.SOL_CASH_WALLET)==[]
    invalid={"programId":fc.SOL_RELAY_DEPOSIT,"data":"xxx"}
    assert fc.solana_events("sig3",sol_tx(fc.SOL_CASH_WALLET,instructions=[invalid]),fc.SOL_CASH_WALLET)==[]


def test_relay_payout_signed_by_solver_and_memo_is_not_a_buy():
    oid="0x"+"2"*64
    ix={"programId":"MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr","parsed":oid}
    tx=sol_tx(fc.SOL_CASH_WALLET,signed=False,cosigned=False,solver=True,
              before=100,after=50_000_100,instructions=[ix])
    rows=fc.solana_events("payout",tx,fc.SOL_CASH_WALLET)
    assert len(rows)==1 and rows[0]["kind"]=="RELAY_PAYOUT"
    assert rows[0]["order_id"]==oid and rows[0]["amount_raw"]=="50000000"
    assert rows[0]["signal_eligible"] is False


def test_unsigned_fomo_cosigner_receipt_is_not_a_market_buy():
    tx=sol_tx(fc.SOL_CASH_WALLET,signed=False,cosigned=True,
              before=0,after=1000000)
    assert fc.solana_events("other",tx,fc.SOL_CASH_WALLET)==[]


def test_solana_samechain_candidate_not_final_trade():
    wallet=fc.SOL_CANDIDATE_WALLET
    tx=sol_tx(wallet,before=5_000_000,after=0,
              instructions=[{"programId":"DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH"}])
    tx["meta"]["postTokenBalances"].append({
        "accountIndex":3,"mint":"TokenABC","owner":wallet,
        "uiTokenAmount":{"amount":"100000000","decimals":9},
    })
    rows=fc.solana_events("swap_candidate",tx,wallet)
    assert len(rows)==1 and rows[0]["kind"]=="SWAP_CANDIDATE"
    assert rows[0]["signal_eligible"] is False


def test_evm_fill_requires_router_and_executor_transfer():
    wallet=fc.RH_CANDIDATE_WALLET
    oid="0x"+"3"*64
    token="0x"+"a"*40
    receipt={"transactionHash":"0x"+"f"*64,"status":"0x1",
        "logs":[log(1,token,[fc.TOPIC_TRANSFER,topic(fc.RH_RELAY_EXECUTOR),topic(wallet)],
                    data_words(123456))]}
    tx={"to":fc.RH_RELAY_ROUTER,"input":"0xabcdef"+oid[2:],"hash":"0x"+"f"*64}
    rows=fc.robinhood_buy_fills(tx,receipt,wallet)
    assert len(rows)==1 and rows[0]["kind"]=="BUY_FILL"
    assert rows[0]["amount_raw"]=="123456" and rows[0]["order_id"]==oid
    assert rows[0]["signal_eligible"] is False
    assert fc.robinhood_buy_fills({**tx,"to":"0x"+"b"*40},receipt,wallet)==[]


def test_evm_sell_belongs_only_to_correct_4337_operation_in_shared_bundle():
    wallet=fc.RH_CANDIDATE_WALLET
    other="0x"+"b"*40
    token="0x"+"a"*40
    oid="0x"+"4"*64
    log_list=[
        log(1,token,[fc.TOPIC_TRANSFER,topic(other),topic(fc.RH_RELAY_DEPOSITORY)],data_words(111)),
        log(2,fc.RH_ENTRYPOINT,[fc.TOPIC_USEROP,"0x"+"0"*64,topic(other)],data_words(1,1,0,0)),
        log(3,token,[fc.TOPIC_TRANSFER,topic(wallet),topic(fc.RH_RELAY_DEPOSITORY)],data_words(100)),
        log(4,fc.RH_RELAY_DEPOSITORY,[fc.TOPIC_DEPOSIT],
            data_words(wallet,fc.RH_USDG,2500000,oid)),
        log(5,fc.RH_ENTRYPOINT,[fc.TOPIC_USEROP,"0x"+"0"*64,topic(wallet)],data_words(1,1,0,0)),
    ]
    receipt={"transactionHash":"0x"+"9"*64,"status":"0x1","logs":log_list}
    rows=fc.robinhood_user_operations(receipt,wallet)
    assert len(rows)==1
    assert rows[0]["kind"]=="SELL_EXECUTED"
    assert rows[0]["asset"]==token
    assert rows[0]["order_id"]==oid
    receipt["logs"][4]["data"]=data_words(1,0,0,0)
    assert fc.robinhood_user_operations(receipt,wallet)==[]


def test_multi_token_or_multi_order_not_wrongly_called_sell():
    wallet=fc.RH_CANDIDATE_WALLET
    logs=[
        log(1,"0x"+"a"*40,[fc.TOPIC_TRANSFER,topic(wallet),topic("0x"+"b"*40)],data_words(100)),
        log(2,"0x"+"c"*40,[fc.TOPIC_TRANSFER,topic(wallet),topic("0x"+"d"*40)],data_words(200)),
        log(3,fc.RH_ENTRYPOINT,[fc.TOPIC_USEROP,"0x"+"0"*64,topic(wallet)],data_words(1,1,0,0)),
    ]
    receipt={"transactionHash":"0x"+"9"*64,"logs":logs}
    rows=fc.robinhood_user_operations(receipt,wallet)
    assert len(rows)==1 and rows[0]["kind"]=="USEROP_AMBIGUOUS"


def test_cross_chain_relay_join_is_exact_unique_and_not_followable():
    oid="0x"+"f"*64
    pay={"kind":"RELAY_PAY","order_id":oid,"chain":"SOL","asset":fc.USDC,"tx_id":"sol1",
         "reason":"FOMO_COSIGNED_RELAY_DEPOSIT"}
    fill={"kind":"BUY_FILL","order_id":oid,"chain":"RH","asset":"0x"+"a"*40,"tx_id":"rh1"}
    other={"kind":"RELAY_PAY","order_id":"0x"+"e"*64,"chain":"SOL","asset":fc.USDC,"tx_id":"sol2"}
    joined=fc.pair_orders([pay,fill,other])
    assert len(joined)==2
    good=next(x for x in joined if x["order_id"]==oid)
    assert good["kind"]=="PAIRED_BUY_EVIDENCE"
    assert good["attribution"]=="THIRD_PARTY_UNVERIFIED"
    assert good["follow_signal_eligible"] is False
    assert good["rh_token_contract"]=="0x"+"a"*40
    assert good["rh_token_decimals"] is None
    assert good["solana_cash_decimals"]==6
    dup=fc.pair_orders([pay,fill,{**fill,"tx_id":"rh2"}])
    assert dup[0]["kind"]=="INCOMPLETE_OR_AMBIGUOUS_ORDER"


def test_two_leg_sell_is_not_a_buy():
    oid="0x"+"f"*64
    joined=fc.pair_orders([
        {"kind":"SELL_EXECUTED","order_id":oid,"chain":"RH","asset":"token","tx_id":"evm"},
        {"kind":"RELAY_PAYOUT","order_id":oid,"chain":"SOL","asset":fc.USDC,"tx_id":"sol"},
    ])
    assert joined[0]["kind"]=="PAIRED_SELL_EVIDENCE"


def test_unrecognized_order_id_is_never_paired():
    assert fc.order_id("0x"+"0"*64) is None
    assert fc.order_id("broken") is None
    assert fc.pair_orders([{"kind":"RELAY_PAY","order_id":None}])==[]


def test_collector_requires_true_rpc_completeness(monkeypatch):
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="module_unit_test")
    class NoPage:
        def call(self,method,params):
            if method=="getSignaturesForAddress":
                return [{"signature":str(i),"slot":10,"blockTime":999} for i in range(1000)]
            if method=="getTransaction":
                return None
            raise AssertionError(method)
    monkeypatch.setitem(audit["solana_signatures"].__globals__,"MAX_SOL_PAGES",1)
    with pytest.raises(audit["IncompleteWindow"]):
        audit["solana_signatures"](NoPage(),"wallet",10,1000)
    assert audit["pad_evm_wallet"](fc.RH_CANDIDATE_WALLET).endswith(fc.RH_CANDIDATE_WALLET[2:])


def test_audit_never_exposes_unverified_identity_as_signal():
    assert fc.RH_CHAIN_ID==4663
    assert fc.FOMO_EIP7702_CODE.startswith("0xef0100")
    assert fc.RH_CANDIDATE_WALLET.lower()=="0x696d1265c8fc4f14797abebfae3c43ebfa9d8e28"

def test_exact_historical_window_excludes_newer_solana_events():
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="historical_window_test")
    class RPC:
        def call(self,method,params):
            assert method=="getSignaturesForAddress"
            return [
                {"signature":"newer","slot":4,"blockTime":120},
                {"signature":"in-window","slot":3,"blockTime":110},
                {"signature":"older","slot":2,"blockTime":95},
            ]
    found=audit["solana_signatures"](RPC(),"wallet",100,115)
    assert [x["signature"] for x in found]==["in-window"]


def test_historical_evm_block_window_is_bounded_above():
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="historical_rh_test")
    class RPC:
        def call(self,method,params):
            if method=="eth_blockNumber":
                return "0x5"
            assert method=="eth_getBlockByNumber"
            return {"timestamp":hex(int(params[0],16)*5)}
    assert audit["rh_block_number"](RPC(),11,20)==(3,4)

def test_rpc_rate_limit_diagnostic_never_leaks_api_credentials(monkeypatch):
    import urllib.error
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="http_rate_limit_test")
    class FakeHTTP:
        def __init__(self): self.calls=0
        def __call__(self, request, timeout):
            self.calls+=1
            raise urllib.error.HTTPError(
                "https://private-rpc.example/api/SECRETKEY",429,"rate limit",None,None)
    fake=FakeHTTP()
    monkeypatch.setitem(audit["RPC"].call.__globals__,"RPC_RETRY_DELAYS_SECONDS",())
    monkeypatch.setattr(audit["urllib"].request,"urlopen",fake)
    rpc=audit["RPC"]("https://private-rpc.example/api/SECRETKEY")
    with pytest.raises(audit["IncompleteWindow"]) as err:
        rpc.call("getTransaction",["fake",{}])
    assert audit["safe_error"](err.value)=="RPC_HTTP_429"
    assert "SECRETKEY" not in str(err.value)
    assert rpc.last_method=="getTransaction"
    assert fake.calls==1


def test_finalized_solana_cache_survives_partial_rpc_retry(tmp_path):
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="cache_test")
    cache=audit["SignatureCache"](tmp_path/"frank-fomo-cache")
    wallet=fc.SOL_CASH_WALLET
    sig="2"*88
    tx=sol_tx(wallet,cosigned=False,instructions=[])
    cache.save(wallet,sig,tx["slot"],tx)
    read=cache.load(wallet,sig,tx["slot"])
    assert read==tx and cache.hits==1 and cache.writes==1
    assert cache.load(wallet,sig,999) is None
    assert cache.load(wallet,"not-a-signature",tx["slot"]) is None
    file=tmp_path/"frank-fomo-cache"/wallet/(sig+".json")
    assert file.stat().st_mode & 0o077 == 0
    assert (tmp_path/"frank-fomo-cache"/wallet).stat().st_mode & 0o077 == 0


def test_candidate_rh_wallet_eoa_is_visible_but_not_verified():
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="eoa_wallet_test")
    class RPC:
        def __init__(self): self.calls=0; self.scan_stage=""; self.progress={}
        def call(self,method,params):
            self.calls+=1
            if method=="eth_chainId": return hex(fc.RH_CHAIN_ID)
            if method=="eth_getCode": return "0x"
            if method=="eth_blockNumber": return "0x5"
            if method=="eth_getBlockByNumber":
                return {"timestamp":hex(int(params[0],16)*5)}
            if method=="eth_getLogs": return []
            raise AssertionError(method)
    result=audit["scan_robinhood"](RPC(),fc.RH_CANDIDATE_WALLET,11,20)
    assert result["status"]=="COMPLETE"
    assert result["wallet_code_status"]=="EOA"
    assert result["eip7702_delegation_confirmed"] is False
    assert result["userop_tx_count"]==0
    assert result["inbound_transfer_tx_count"]==0


def test_live_audit_partial_report_has_reason_method_and_progress_no_url(monkeypatch):
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="partial_report_test")
    funcs=audit["audit"].__globals__
    class RPC:
        def __init__(self,url):
            self.scan_stage="INIT";self.last_method="NONE";self.calls=0
            self.progress={}
    def fail_solana(rpc,wallet,since,until,cache=None):
        rpc.scan_stage="SOL_GET_TRANSACTION"
        rpc.last_method="getTransaction"
        rpc.calls=57
        rpc.progress={"signatures_in_window":173,"transactions_decoded":55}
        raise audit["IncompleteWindow"]("RPC_HTTP_429")
    def fail_rh(rpc,wallet,since,until):
        rpc.scan_stage="RH_INBOUND_ERC20_LOGS"
        rpc.last_method="eth_getLogs"
        rpc.calls=7
        rpc.progress={"log_chunks_completed":3}
        raise audit["IncompleteWindow"]("RPC_ERROR_-32062")
    monkeypatch.setitem(funcs,"RPC",RPC)
    monkeypatch.setitem(funcs,"scan_solana",fail_solana)
    monkeypatch.setitem(funcs,"scan_robinhood",fail_rh)
    report=audit["audit"](24,["https://private/SECRETKEY"],
                          "https://robinhood.rpc",1791472854)
    assert report["status"]=="PARTIAL"
    assert len(report["chains"])==3
    assert report["chains"][0]["diagnostics"][0]=={
        "reason":"RPC_HTTP_429","stage":"SOL_GET_TRANSACTION",
        "method":"getTransaction","rpc_calls":57,
        "signatures_in_window":173,"transactions_decoded":55}
    assert report["chains"][2]["diagnostics"][0]["reason"]=="RPC_ERROR_-32062"
    assert "SECRETKEY" not in str(report)
    assert report["paired"]==[]
    assert report["production_db_writes"]==0
    assert report["gmail_sent"]==0


def test_rh_log_http_rate_limit_does_not_recursively_split(monkeypatch):
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="log_rate_limit_test")
    class RPC:
        def __init__(self):
            self.progress={}; self.calls=0
        def call(self,method,params):
            self.calls+=1
            raise audit["IncompleteWindow"]("RPC_HTTP_429")
    rpc=RPC()
    with pytest.raises(audit["IncompleteWindow"],match="RPC_HTTP_429"):
        audit["rh_getlogs"](rpc,100,100000,[fc.TOPIC_TRANSFER])
    assert rpc.calls==1



def test_solana_v1_tx_decode_pinned_and_compatible_with_jsonparsed_cache(tmp_path):
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="sol_v1_test")
    wallet=fc.SOL_CASH_WALLET
    sig="3"*88
    tx=sol_tx(wallet,cosigned=False)
    tx["version"]=1
    seen=[]
    class RPC:
        def __init__(self):
            self.scan_stage="";self.progress={};self.calls=0;self.last_method="NONE"
        def call(self,method,params):
            self.calls+=1;self.last_method=method
            if method=="getSignaturesForAddress":
                return [{"signature":sig,"slot":1212,"blockTime":110}]
            if method=="getTransaction":
                version=params[1].get("maxSupportedTransactionVersion")
                seen.append(version)
                if version!=1:
                    raise audit["IncompleteWindow"]("RPC_ERROR_-32015")
                assert params[1]["encoding"]=="jsonParsed"
                return tx
            raise AssertionError(method)
    cache=audit["SignatureCache"](tmp_path/"cached")
    first=audit["scan_solana"](RPC(),wallet,100,115,cache=cache)
    assert first["status"]=="COMPLETE"
    assert first["signatures_scanned"]==1
    assert seen==[1]
    assert cache.writes==1
    second=audit["scan_solana"](RPC(),wallet,100,115,cache=cache)
    assert second["status"]=="COMPLETE"
    assert second["cache_hits"]==1
    assert seen==[1]  # cached retry must not make a second getTransaction call


def test_robinhood_fallback_403_then_publicnode_no_key_url_logged(monkeypatch):
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="rh_fallback_test")
    gl=audit["audit"].__globals__
    visited=[]
    class RPC:
        def __init__(self,url):
            self.url=url;self.calls=0;self.last_method="eth_chainId"
            self.scan_stage="RH_CHAIN_ID";self.progress={}
    def sol(rpc,wallet,cutoff,until,cache=None):
        return {"chain":"SOL","wallet":wallet,"status":"COMPLETE",
                "signatures_scanned":0,"legs":[]}
    def rh(rpc,wallet,cutoff,until):
        visited.append(rpc.url)
        if "rpc.mainnet.chain.robinhood.com" in rpc.url:
            raise audit["IncompleteWindow"]("RPC_HTTP_403")
        return {"chain":"RH","wallet":wallet,"status":"COMPLETE",
                "wallet_code_status":"OTHER_DELEGATION",
                "eip7702_delegation_confirmed":False,"legs":[]}
    monkeypatch.setitem(gl,"RPC",RPC)
    monkeypatch.setitem(gl,"scan_solana",sol)
    monkeypatch.setitem(gl,"scan_robinhood",rh)
    report=audit["audit"](24,["https://solana.secret.example/KEY"],None,1791472854)
    assert report["status"]=="RPC_WINDOW_COMPLETE_IDENTITY_UNVERIFIED"
    assert visited==list(audit["DEFAULT_RH_RPCS"])
    assert "secret" not in str(report).lower()
    assert report["chains"][-1]["eip7702_delegation_confirmed"] is False
    assert report["paired"]==[]


def test_robinhood_all_rpc_403_fail_closed_with_two_reasons(monkeypatch):
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="rh_all_denied_test")
    gl=audit["audit"].__globals__
    class RPC:
        def __init__(self,url):
            self.calls=1;self.scan_stage="RH_CHAIN_ID"
            self.last_method="eth_chainId";self.progress={}
    def sol(rpc,wallet,cutoff,until,cache=None):
        return {"chain":"SOL","wallet":wallet,"status":"COMPLETE","legs":[]}
    def rh(rpc,wallet,cutoff,until):
        raise audit["IncompleteWindow"]("RPC_HTTP_403")
    monkeypatch.setitem(gl,"RPC",RPC)
    monkeypatch.setitem(gl,"scan_solana",sol)
    monkeypatch.setitem(gl,"scan_robinhood",rh)
    report=audit["audit"](24,["https://solana.example"],None,1791472854)
    rh_item=report["chains"][-1]
    assert report["status"]=="PARTIAL"
    assert rh_item["endpoint_trials"]==2
    assert [x["reason"] for x in rh_item["diagnostics"]]==["RPC_HTTP_403","RPC_HTTP_403"]
    assert not report["paired"]



def test_reuse_alchemy_key_only_across_exact_official_hosts():
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="alchemy_derive_test")
    good="https://solana-mainnet.g.alchemy.com/v2/LOCAL_TEST_KEY123"
    bad=[
        "https://solana-mainnet.g.alchemy.com.evil.example/v2/LOCAL_TEST_KEY123",
        "https://solana-mainnet.g.alchemy.com:444/v2/LOCAL_TEST_KEY123",
        "http://solana-mainnet.g.alchemy.com/v2/LOCAL_TEST_KEY123",
        "https://solana-mainnet.g.alchemy.com/v2/LOCAL_TEST_KEY123?redirect=evil",
        "https://solana-mainnet.g.alchemy.com/token/LOCAL_TEST_KEY123",
        "https://solana-mainnet.other-provider.com/v2/LOCAL_TEST_KEY123",
    ]
    result=audit["derive_robinhood_alchemy_rpcs"]([*bad,good,good])
    assert result==["https://robinhood-mainnet.g.alchemy.com/v2/LOCAL_TEST_KEY123"]
    assert all("evil.example" not in v for v in result)


def test_optional_robinhood_private_rpc_file_requires_owner_only(tmp_path):
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="rh_file_test")
    cfg=tmp_path/"robinhood_rpc_urls"
    url="https://robinhood-mainnet.g.alchemy.com/v2/TESTKEY123456"
    assert audit["configured_robinhood_rpc_file"](cfg)==[]
    cfg.write_text(url)
    cfg.chmod(0o644)
    with pytest.raises(audit["IncompleteWindow"],match="PERMISSIONS_UNSAFE"):
        audit["configured_robinhood_rpc_file"](cfg)
    cfg.chmod(0o600)
    assert audit["configured_robinhood_rpc_file"](cfg)==[url]
    link=tmp_path/"alias"
    link.symlink_to(cfg)
    with pytest.raises(audit["IncompleteWindow"],match="SYMLINK_UNSAFE"):
        audit["configured_robinhood_rpc_file"](link)


def test_authenticated_provider_preferred_and_report_never_prints_key(monkeypatch):
    script=Path(__file__).resolve().parents[1]/"scripts/audit_frank_fomo_crosschain.py"
    audit=runpy.run_path(str(script),run_name="provider_preference_test")
    globals_=audit["audit"].__globals__
    chosen=[]
    class RPC:
        def __init__(self,url):
            self.url=url
            self.calls=0;self.scan_stage="INIT";self.last_method="NONE";self.progress={}
    def sol(rpc,wallet,cutoff,until,cache=None):
        return {"chain":"SOL","wallet":wallet,"status":"COMPLETE",
                "signatures_scanned":0,"legs":[]}
    def rh(rpc,wallet,cutoff,until):
        chosen.append(rpc.url)
        return {"chain":"RH","wallet":wallet,"status":"COMPLETE",
                "eip7702_delegation_confirmed":True,"legs":[]}
    monkeypatch.setitem(globals_,"RPC",RPC)
    monkeypatch.setitem(globals_,"scan_solana",sol)
    monkeypatch.setitem(globals_,"scan_robinhood",rh)
    secret="https://robinhood-mainnet.g.alchemy.com/v2/LOCAL_TEST_KEY123"
    result=audit["audit"](24,["https://solana.example"],None,1791472854,
                          rh_extra_urls=[secret])
    assert chosen==[secret]
    assert result["status"]=="RPC_WINDOW_COMPLETE_IDENTITY_UNVERIFIED"
    assert result["rh_provider_diagnostics"]["authenticated_provider_configured"]
    assert "LOCAL_TEST_KEY123" not in str(result)
    assert result["promotion_to_follow_signals"]=="FORBIDDEN"
