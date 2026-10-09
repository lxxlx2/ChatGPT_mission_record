"""Focused tests for immutable, resumable, request-budgeted Frank research only."""
from __future__ import annotations

import json
import urllib.error

import pytest

from scripts import audit_frank_native_resume as scan


ACCOUNT="7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG"
OTHER="6HEFmhrdC8KxY4e4C5eg4nmaQNRGyMAcwuMEeMpJTGV7"
MINT="HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy"
ROOT=scan.WALLET
CHARS="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def sig(index):
    out=""
    n=index+1
    while n:
        n,rest=divmod(n,58)
        out=CHARS[rest]+out
    return "1"*(88-len(out))+out


def context(accounts=None):
    return {
        "version":scan.VERSION,"wallet":ROOT,
        "start":scan.START,"end":scan.END,
        "source_sha256":"a"*64,"root_tx_sha256":"b"*64,
        "root_count":173,"commitment":"finalized",
        "page_size":scan.PAGE_SIZE,
        "max_signatures":scan.MAX_SOL_TRANSACTIONS_PER_WALLET,
        "max_pages":scan.MAX_SOL_PAGES,
        "max_extra_decode":scan.MAX_ADDITIONAL_TRANSACTIONS,
        "inventory":accounts or {ACCOUNT:MINT},
    }


def row(i,at):
    return {"signature":sig(i),"slot":400000+i,"blockTime":at,"err":None}


def test_default_plan_uses_only_local_state_no_network_or_files(tmp_path,monkeypatch):
    def blocked(*args,**kwargs):
        raise AssertionError("unwanted network")
    monkeypatch.setattr(scan,"one_rpc",blocked)
    root=tmp_path/"checkpoints"
    store=scan.Checkpoints(root,context(),create=False)
    counts,stopped=scan.do_run(store,set(),"plan",False,0)
    report=scan.report(store,set(),set(),counts,stopped)
    assert not root.exists()
    assert counts["rpc_attempts"]==0
    assert report["accounts_total"]==1
    assert report["accounts_complete"]==0
    assert report["status"]=="OBSERVED_SCOPE_PARTIAL"
    assert report["full_person_trade_coverage"] is False


def test_page_cursor_restarts_after_429_with_no_duplicate_calls(tmp_path,monkeypatch):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    first_page=[row(i,scan.END-i-5) for i in range(scan.PAGE_SIZE)]
    later_page=[row(scan.PAGE_SIZE,scan.START-5)]
    calls=[]
    def rpc(_url,method,params):
        calls.append((method,params))
        if len(calls)==1:
            return first_page
        if len(calls)==2:
            raise scan.ScanBlocked("RPC_HTTP_429")
        assert params[1]["before"]==first_page[-1]["signature"]
        return later_page
    monkeypatch.setattr(scan,"one_rpc",rpc)
    c1,reason1=scan.do_run(store,set(),"signatures",True,1,"https://example.invalid")
    assert c1["rpc_attempts"]==1 and reason1=="REQUEST_BUDGET_EXHAUSTED"
    s1=store.account(ACCOUNT)
    assert s1["status"]=="ACTIVE" and s1["pages"]==1
    assert len(s1["rows"])==scan.PAGE_SIZE
    c2,reason2=scan.do_run(store,set(),"signatures",True,2,"https://example.invalid")
    assert c2["rpc_attempts"]==1 and reason2=="RPC_HTTP_429"
    assert store.account(ACCOUNT)==s1
    reopened=scan.Checkpoints(store.root,context(),create=True)
    c3,reason3=scan.do_run(reopened,set(),"signatures",True,2,"https://example.invalid")
    assert reason3 is None and c3["rpc_attempts"]==1
    state=reopened.account(ACCOUNT)
    assert state["status"]=="COMPLETE"
    assert len(state["rows"])==scan.PAGE_SIZE
    assert len(calls)==3
    assert all("before" not in calls[0][1][1] for _ in range(1))
    assert calls[1][1][1]["before"]==first_page[-1]["signature"]
    assert calls[2][1][1]["before"]==first_page[-1]["signature"]
    assert reopened.manifest.stat().st_mode & 0o077==0
    assert (reopened.root/("account-"+ACCOUNT+".json")).stat().st_mode & 0o077==0


def test_cap_kept_at_original_1000_and_never_called_again(tmp_path,monkeypatch):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    calls=[]
    def rpc(_url,method,params):
        calls.append(params)
        n=(len(calls)-1)*scan.PAGE_SIZE
        return [row(i,scan.END-i-1) for i in range(n,n+scan.PAGE_SIZE)]
    monkeypatch.setattr(scan,"one_rpc",rpc)
    for _ in range(3):
        counts,reason=scan.do_run(store,set(),"signatures",True,4,"https://example.invalid")
    item=store.account(ACCOUNT)
    assert item["status"]=="CAPPED"
    assert len(item["rows"])==1000
    assert len(calls)==4
    before=len(calls)
    counts,reason=scan.do_run(store,set(),"signatures",True,2,"https://example.invalid")
    assert counts["rpc_attempts"]==0
    assert len(calls)==before
    report=scan.report(store,set(),set(),counts,reason)
    assert report["accounts_capped"][ACCOUNT]["status"]=="INCOMPLETE_LIMIT"
    assert report["full_person_trade_coverage"] is False


def test_tampered_checkpoint_and_changed_source_context_fail_closed(tmp_path):
    base=tmp_path/"checkpoint"
    store=scan.Checkpoints(base,context(),create=True)
    state=store.account(ACCOUNT)
    store.save_account(state)
    file=base/("account-"+ACCOUNT+".json")
    obj=json.loads(file.read_text())
    obj["status"]="COMPLETE"
    file.write_text(json.dumps(obj))
    with pytest.raises(scan.ScanBlocked,match="CHECKPOINT_HASH_MISMATCH"):
        store.account(ACCOUNT)
    new_context=context()
    new_context["source_sha256"]="c"*64
    with pytest.raises(scan.ScanBlocked,match="CHECKPOINT_CONTEXT_MISMATCH"):
        scan.Checkpoints(base,new_context,create=True)


def test_page_timestamp_and_signature_validation_never_commit_corrupt_page(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    state=store.account(ACCOUNT)
    bad=[row(0,scan.START+20),row(1,scan.START+25)]
    with pytest.raises(scan.ScanBlocked,match="SIGNATURE_TIME_ORDER_INVALID"):
        scan.scan_page(state,lambda *args:bad)
    assert store.account(ACCOUNT)["status"]=="PENDING"
    bad2=[row(0,scan.START+30),row(0,scan.START+25)]
    with pytest.raises(scan.ScanBlocked,match="SIGNATURE_PAGE_DUPLICATE"):
        scan.scan_page(state,lambda *args:bad2)


def test_decode_receipt_durable_and_second_run_zero_rpc(tmp_path,monkeypatch):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    state=store.account(ACCOUNT)
    state.update({"status":"COMPLETE","pages":1,
                  "before":sig(0),"rows":[row(0,scan.START+25)]})
    store.save_account(state)
    def mk_tx():
        quote_account=OTHER
        def bal(idx,mint,raw):
            return {"accountIndex":idx,"mint":mint,"owner":ROOT,
                    "uiTokenAmount":{"amount":str(raw),"decimals":6}}
        return {
            "slot":400000,"blockTime":scan.START+25,
            "transaction":{"message":{"accountKeys":[
                {"pubkey":ROOT,"signer":False},
                {"pubkey":ACCOUNT,"signer":False},
                {"pubkey":quote_account,"signer":False}
            ],"instructions":[]}},
            "meta":{"err":None,
                "preTokenBalances":[bal(1,MINT,0),bal(2,scan.flows.__globals__["USDC"],10000)],
                "postTokenBalances":[bal(1,MINT,500),bal(2,scan.flows.__globals__["USDC"],9000)],
                "innerInstructions":[]}
        }
    calls=[]
    def rpc(_url,method,params):
        calls.append(method)
        assert method=="getTransaction"
        return mk_tx()
    monkeypatch.setattr(scan,"one_rpc",rpc)
    first,stop=scan.do_run(store,set(),"decode",True,2,"https://example.invalid")
    assert stop is None and first["new_receipts"]==1 and calls==["getTransaction"]
    receipt=store.receipt(sig(0))
    assert receipt["trade_confirmed"] is False
    assert receipt["opposing_flow"] is True
    reopened=scan.Checkpoints(store.root,context(),create=True)
    second,stop=scan.do_run(reopened,set(),"decode",True,2,"https://example.invalid")
    assert stop is None and second["rpc_attempts"]==0
    assert calls==["getTransaction"]


def test_rpc_rate_limit_is_single_attempt_and_does_not_reveal_url(monkeypatch):
    def error(*args,**kwargs):
        raise urllib.error.HTTPError("https://example.invalid/secret-key",429,"too many",{},None)
    monkeypatch.setattr(scan.urllib.request,"urlopen",error)
    with pytest.raises(scan.ScanBlocked,match="RPC_HTTP_429") as e:
        scan.one_rpc("https://example.invalid/secret-key","getSignaturesForAddress",[])
    assert "secret-key" not in str(e.value)


def test_no_network_without_explicit_permission(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    with pytest.raises(scan.ScanBlocked,match="EXPLICIT_NETWORK_PERMISSION_REQUIRED"):
        scan.do_run(store,set(),"signatures",False,1)


def test_decoding_rejects_wrong_block_time_for_matching_slot():
    item=row(4,scan.START+30)
    tx={
        "slot":item["slot"],"blockTime":scan.START+31,
        "transaction":{"message":{"accountKeys":[],"instructions":[]}},
        "meta":{"err":None,"preTokenBalances":[],"postTokenBalances":[]},
    }
    with pytest.raises(scan.ScanBlocked,match="DECODE_TRANSACTION_MISMATCH"):
        scan.decode_tx(item,lambda *args:tx)


def test_json_rpc_rate_limit_is_not_retried_or_recorded(monkeypatch,tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    requests=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read(self,*args):return b'{"jsonrpc":"2.0","id":1,"error":{"code":-32005,"message":"limit"}}'
    def fake_urlopen(request,timeout):
        requests.append(request)
        return Response()
    monkeypatch.setattr(scan.urllib.request,"urlopen",fake_urlopen)
    counts,reason=scan.do_run(store,set(),"signatures",True,3,
                              "https://example.invalid/PRIVATE")
    assert counts["rpc_attempts"]==1
    assert reason=="RPC_RATE_LIMIT"
    assert len(requests)==1
    assert store.account(ACCOUNT)["status"]=="PENDING"


def test_explicit_network_scan_respects_minimum_spacing(monkeypatch,tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    PAGE=scan.PAGE_SIZE
    rows=[row(i,scan.END-i-1) for i in range(PAGE)]
    clock={"t":100.0,"waited":[]}
    monkeypatch.setattr(scan.time,"monotonic",lambda:clock["t"])
    def sleep(seconds):
        clock["waited"].append(seconds)
        clock["t"]+=seconds
    monkeypatch.setattr(scan.time,"sleep",sleep)
    responses=[rows,[row(PAGE,scan.START-5)]]
    def fake_rpc(*args):
        assert responses
        return responses.pop(0)
    monkeypatch.setattr(scan,"one_rpc",fake_rpc)
    counts,reason=scan.do_run(store,set(),"signatures",True,2,
                              "https://example.invalid")
    assert reason is None
    assert counts["rpc_attempts"]==2
    assert clock["waited"]==[scan.MIN_REQUEST_INTERVAL_SECONDS]
    assert store.account(ACCOUNT)["status"]=="COMPLETE"


def test_checkpoint_with_valid_hash_but_invalid_account_rows_fails_closed(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    state=store.account(ACCOUNT)
    state.update({"status":"ACTIVE","pages":1,"before":sig(1),
                  "rows":[row(0,scan.END-5),{"signature":123,"slot":10,"blockTime":scan.END-10}]})
    store.save_account(state)
    with pytest.raises(scan.ScanBlocked,match="ACCOUNT_ROWS_INVALID"):
        store.account(ACCOUNT)


def test_saved_page_requires_nonincreasing_history_across_resume(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    state=store.account(ACCOUNT)
    state.update({"status":"ACTIVE","pages":1,"before":sig(0),
                  "rows":[row(0,scan.START+10)]})
    store.save_account(state)
    with pytest.raises(scan.ScanBlocked,match="SIGNATURE_TIME_ORDER_INVALID"):
        scan.scan_page(store.account(ACCOUNT),lambda *args:[row(1,scan.START+20)])
    assert store.account(ACCOUNT)["rows"]==state["rows"]


def test_report_refuses_wrong_slot_in_validly_hashed_receipt(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    state=store.account(ACCOUNT)
    state.update({"status":"COMPLETE","pages":1,"before":sig(0),
                  "rows":[row(0,scan.START+25)]})
    store.save_account(state)
    rcpt={"context":store.key,"signature":sig(0),"slot":999,
          "tx_sha256":"a"*64,"opposing_flow":False,
          "root_referenced":False,"fomo_cosigned":False,"target_mints":[]}
    store._write(store.root/("receipt-"+sig(0)+".json"),rcpt)
    with pytest.raises(scan.ScanBlocked,match="RECEIPT_EVIDENCE_INVALID"):
        scan.report(store,set(),set(),{"rpc_attempts":0,"new_signature_pages":0,
                                       "new_receipts":0},None)


def test_explicit_one_account_rpc_selection_cannot_scan_others(tmp_path,monkeypatch):
    store=scan.Checkpoints(tmp_path/"checkpoint",
        context({ACCOUNT:MINT,OTHER:scan.flows.__globals__["USDC"]}),create=True)
    calls=[]
    def fake_rpc(_url,method,params):
        calls.append(params[0])
        return [row(0,scan.START+20)]
    monkeypatch.setattr(scan,"one_rpc",fake_rpc)
    counters,reason=scan.do_run(
        store,set(),"signatures",True,1,"https://example.invalid",account=ACCOUNT
    )
    assert reason is None
    assert counters["rpc_attempts"]==1
    assert calls==[ACCOUNT]
    assert store.account(ACCOUNT)["status"]=="COMPLETE"
    assert store.account(OTHER)["status"]=="PENDING"


def test_explicit_account_must_come_from_locked_historic_owner_inventory(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    with pytest.raises(scan.ScanBlocked,match="ACCOUNT_OUTSIDE_OBSERVED_INVENTORY"):
        scan.do_run(
            store,set(),"signatures",True,1,"https://example.invalid",
            account=OTHER
        )


def test_zero_rpc_plan_reports_decoded_nonopposing_receipt_identifiers(tmp_path,monkeypatch):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    state=store.account(ACCOUNT)
    state.update({"status":"COMPLETE","pages":1,"before":sig(1),
                  "rows":[row(0,scan.START+25),row(1,scan.START+20)]})
    store.save_account(state)
    for index in (0,1):
        store._write(store.root/("receipt-"+sig(index)+".json"),{
            "context":store.key,"signature":sig(index),
            "slot":400000+index,"tx_sha256":"a"*64,
            "opposing_flow":False,"root_referenced":False,
            "fomo_cosigned":False,
            "target_mints":[MINT],"quote_mints":[],
            "trade_confirmed":False,
        })
    monkeypatch.setattr(scan,"one_rpc",lambda *args:pytest.fail("NETWORK CALLED"))
    counts,stop=scan.do_run(store,set(),"plan",False,0)
    report=scan.report(store,set(),set(),counts,stop)
    assert counts["rpc_attempts"]==0
    assert report["decoded_opposing_flow_review_candidates"]==0
    assert report["decoded_review_sample"]==[]
    assert len(report["decoded_receipt_sample"])==2
    assert {x["signature"] for x in report["decoded_receipt_sample"]}=={sig(0),sig(1)}
    assert all(x["target_mints"]==[MINT] for x in report["decoded_receipt_sample"])
    assert all(x["fomo_cosigned"] is False for x in report["decoded_receipt_sample"])


def test_recent_usdc_page_saves_time_bounds_without_false_complete(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoints",context(),create=True)
    first=[row(i,scan.END+scan.PAGE_SIZE-i) for i in range(scan.PAGE_SIZE)]
    s=scan.scan_page(store.account(ACCOUNT),lambda *_:first)
    assert s["status"]=="ACTIVE"
    assert s["rows"]==[]
    assert s["last_page_size"]==250
    assert s["last_page_oldest_block_time"]==scan.END+1
    store.save_account(s)
    reopened=scan.Checkpoints(store.root,context(),create=True)
    assert reopened.account(ACCOUNT)["before"]==first[-1]["signature"]
    page=[row(scan.PAGE_SIZE,scan.END-1),
          row(scan.PAGE_SIZE+1,scan.START-1)]
    completed=scan.scan_page(reopened.account(ACCOUNT),lambda *_:page)
    assert completed["status"]=="COMPLETE"
    assert len(completed["rows"])==1
    assert completed["rows"][0]["blockTime"]==scan.END-1
    assert completed["last_page_oldest_block_time"]==scan.START-1


def test_newer_only_page_detects_cross_page_time_reversal(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoints",context(),create=True)
    page=[row(i,scan.END+250-i) for i in range(250)]
    s=scan.scan_page(store.account(ACCOUNT),lambda *_:page)
    store.save_account(s)
    invalid=[row(250,scan.END+10)]
    with pytest.raises(scan.ScanBlocked,match="SIGNATURE_TIME_ORDER_INVALID"):
        scan.scan_page(store.account(ACCOUNT),lambda *_:invalid)
    assert store.account(ACCOUNT)==s


def test_existing_page_without_diagnostics_resumes_without_reset(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoints",context(),create=True)
    old=store.account(ACCOUNT)
    old.update({"status":"ACTIVE","pages":1,"before":sig(250),"rows":[]})
    store.save_account(old)
    assert store.account(ACCOUNT)==old
    page=[row(251,scan.END-10)]
    res=scan.scan_page(store.account(ACCOUNT),lambda *_:page)
    assert res["status"]=="COMPLETE"
    assert res["pages"]==2
    assert res["rows"][0]["signature"]==sig(251)
    assert res["last_page_oldest_block_time"]==scan.END-10
    assert store.account(ACCOUNT)["before"]==sig(250)


def test_explicit_five_second_rpc_spacing_for_usdc_resume(tmp_path,monkeypatch):
    store=scan.Checkpoints(tmp_path/"checkpoints",context(),create=True)
    clock={"now":100.0,"sleeps":[]}
    monkeypatch.setattr(scan.time,"monotonic",lambda:clock["now"])
    def fake_sleep(seconds):
        clock["sleeps"].append(seconds)
        clock["now"]+=seconds
    monkeypatch.setattr(scan.time,"sleep",fake_sleep)
    calls=[]
    def fake_rpc(_url,method,params):
        calls.append((method,params[1].get("before")))
        if len(calls)==1:
            return [row(i,scan.END+250-i) for i in range(scan.PAGE_SIZE)]
        return [row(scan.PAGE_SIZE,scan.END-15)]
    monkeypatch.setattr(scan,"one_rpc",fake_rpc)
    c,reason=scan.do_run(store,set(),"signatures",True,2,
                          "https://example.invalid",
                          account=ACCOUNT,spacing_seconds=5)
    assert reason is None
    assert c["rpc_attempts"]==2
    assert c["new_signature_pages"]==2
    assert clock["sleeps"]==[5]
    assert calls[1][1]==sig(249)
    assert store.account(ACCOUNT)["status"]=="COMPLETE"
    assert store.account(ACCOUNT)["rows"][0]["blockTime"]==scan.END-15


@pytest.mark.parametrize("spacing",[0.5,0,-1,float("nan"),float("inf"),61,True])
def test_rpc_spacing_fails_closed_for_invalid_interval(tmp_path,spacing):
    store=scan.Checkpoints(tmp_path/"checkpoints",context(),create=True)
    with pytest.raises(scan.ScanBlocked,match="REQUEST_SPACING_INVALID"):
        scan.do_run(store,set(),"signatures",True,1,
                    "https://example.invalid",spacing_seconds=spacing)


def test_cutoff_page_fully_validates_rows_before_saving_time_bounds(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    invalid=[row(0,scan.START-1),{"signature":None,"blockTime":None,"slot":None}]
    with pytest.raises(scan.ScanBlocked,match="SIGNATURE_ROW_INVALID"):
        scan.scan_page(store.account(ACCOUNT),lambda *_:invalid)
    assert store.account(ACCOUNT)["status"]=="PENDING"


def test_partial_usdc_account_reports_686_unclassified_signatures_offline(tmp_path,monkeypatch):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    state=store.account(ACCOUNT)
    state.update({"status":"ACTIVE","pages":3,"before":sig(685),
                  "rows":[row(i,scan.END-i-1) for i in range(686)]})
    store.save_account(state)
    monkeypatch.setattr(scan,"one_rpc",lambda *a:pytest.fail("NETWORK CALLED"))
    counters,stop=scan.do_run(store,set(),"plan",False,0)
    report=scan.report(store,{sig(0),sig(1)},set(),counters,stop)
    assert report["status"]=="OBSERVED_SCOPE_PARTIAL"
    assert report["extra_signature_candidates_from_completed_accounts"]==0
    partial=report["partial_account_signature_evidence"]
    assert len(partial)==1
    assert partial[0]["saved_window_signatures"]==686
    assert partial[0]["already_in_root_count"]==2
    assert partial[0]["not_in_root_count"]==684
    assert len(partial[0]["unclassified_extra_sample"])==8
    assert partial[0]["scope"]=="PARTIAL_SIGNATURES_ONLY_NOT_DECODED"
    assert report["full_person_trade_coverage"] is False
    assert report["trade_confirmed_by_audit"] is False
    assert counters["rpc_attempts"]==0


def test_usdc_signature_overflow_checkpoints_prefix_and_marks_incomplete(tmp_path,monkeypatch):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    state=store.account(ACCOUNT)
    state.update({"status":"ACTIVE","pages":4,"before":sig(935),
                  "rows":[row(i,scan.END-i-1) for i in range(936)]})
    store.save_account(state)
    page=[row(i,scan.END-i-1) for i in range(936,1186)]
    calls=[]
    def rpc(_url,method,params):
        calls.append(params)
        return page
    monkeypatch.setattr(scan,"one_rpc",rpc)
    counts,reason=scan.do_run(store,set(),"signatures",True,3,
                              "https://example.invalid",account=ACCOUNT)
    assert counts["rpc_attempts"]==1 and reason is None
    after=store.account(ACCOUNT)
    assert after["status"]=="CAPPED"
    assert after["cap_reason"]=="SIGNATURE_LIMIT"
    assert len(after["rows"])==1000
    assert after["unretained_in_window_signatures_on_cap_page"]==186
    assert after["pages"]==5
    assert len(calls)==1
    report=scan.report(store,set(),set(),counts,reason)
    assert report["accounts_capped"][ACCOUNT]["observed_rows"]==1000
    assert report["accounts_capped"][ACCOUNT]["status"]=="INCOMPLETE_LIMIT"
    assert report["extra_signature_candidates_from_completed_accounts"]==0
    assert report["partial_account_signature_evidence"][0]["not_in_root_count"]==1000
    assert report["full_person_trade_coverage"] is False
    again,why=scan.do_run(store,set(),"signatures",True,2,
                          "https://example.invalid",account=ACCOUNT)
    assert again["rpc_attempts"]==0 and why is None


def test_cutoff_page_cannot_be_complete_if_original_signature_cap_overflows(tmp_path):
    store=scan.Checkpoints(tmp_path/"checkpoint",context(),create=True)
    state=store.account(ACCOUNT)
    state.update({"status":"ACTIVE","pages":4,"before":sig(994),
                  "rows":[row(i,scan.START+1000-i) for i in range(995)]})
    store.save_account(state)
    page=[row(i,scan.START+1000-i) for i in range(995,1006)]
    completed=scan.scan_page(store.account(ACCOUNT),lambda *_:page)
    assert completed["status"]=="CAPPED"
    assert len(completed["rows"])==1000
    assert completed["unretained_in_window_signatures_on_cap_page"]==1
    assert completed["cap_reason"]=="SIGNATURE_LIMIT"
