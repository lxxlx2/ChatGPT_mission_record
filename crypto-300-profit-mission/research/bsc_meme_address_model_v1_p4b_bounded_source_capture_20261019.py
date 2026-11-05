#!/usr/bin/env python3
"""One-shot, free/read-only BNB evidence capture for Mission PR #40.

Uses only standard JSON-RPC methods plus Alchemy alchemy_getAssetTransfers.
Requires BSC_RPC_URL (HTTPS); never writes this URL, provider keys or credentials.
No transaction submission, wallet signing, background job, notification or deployment.
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

W877 = "0x877af245c61289b24f0c619a4346cdbc68f1aaac"
WDD = "0xddac928a240bdace3994c2cc0783d4e29a002127"
LEAD = "0x537f00a63d517320ea0107bbf6176325d6913977"
YOU = "0x1bd0d654e44a78d9b20dcf09fa61100013c07777"
CA_B = "0xcc629b954ccf0563838c797d431dd153b35b7777"
CA_A = "0x9ec1c7fc2cbd74ad0f9badd0c6b7e7260e8c7777"
START, END = "0x74f8e34", "0x7a7661c"
ROUNDS = [
    {"label": "DDAC_FACHE_B", "ca": CA_B, "buy_block": "0x7a6fd0c",
     "sell_block": "0x7a6fe0c", "buy_indices": [4, 5], "sell_indices": [26, 27, 28, 29],
     "buy_hash": "0x94661468eed6746d78f6e6b6e7f5a7859f8670f3fb3b7a26290ff45543903971",
     "sell_hash": "0xaae6d6aa8c5de35acf9a7e56c38aaec871fc09971dea5490d94612f884fd6f8d"},
    {"label": "DDAC_FACHE_A", "ca": CA_A, "buy_block": "0x7a6fe44",
     "sell_block": "0x7a6ff5c", "buy_indices": [8, 9], "sell_indices": [2, 3, 4, 5],
     "buy_hash": "0x48a1b33873be017f0c8506c81cfce5797028cdfdd92a43de73f8681d271dfe03",
     "sell_hash": "0xcee9ee0722a29699906a8acaefbfa568b924ae805392ad385e0deec3a674a22e"},
]
YOULI_BUYS = [
    "0xbe33b237cfd0b5583f41a8dc177131d161148c9c3b5bf43465b92e897e4be2f8",
    "0xcf8ee07f5ccf231ba72730690905feea0305361cd10066c4d8834d2680b727e3",
    "0x241000263b5d2aaeffef5b0c3c92230624df67e3d75fbfbc5cedc495350adac5",
]
EXPECTED_YOULI = {"in": 20702771945057607690441227,
                  "out": 8869110650471634260184494,
                  "remaining": 11833661294585973430256733}
UTC = lambda: datetime.now(timezone.utc).isoformat(timespec="microseconds")

class ArchiveRPC:
    def __init__(self, url):
        p = urllib.parse.urlsplit(url)
        if p.scheme != "https" or not p.hostname or p.username or p.password or p.fragment:
            raise ValueError("BSC_RPC_URL must be an HTTPS RPC endpoint without userinfo/fragment")
        self.url, self.records = url, []
        self.count = 0

    def call(self, kind, method, params):
        if self.count >= 140:
            raise RuntimeError("bounded evidence request budget exhausted")
        self.count += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": self.count, "method": method,
                              "params": params}, separators=(",", ":")).encode()
        req = urllib.request.Request(self.url, payload, {"Content-Type": "application/json"},
                                     method="POST")
        began = UTC()
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=25) as res:
                    body = res.read(4_000_001)
                if len(body) > 4_000_000:
                    raise RuntimeError("provider response exceeded bounded size")
                break
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 502, 503) or attempt == 2:
                    raise RuntimeError("RPC HTTP status " + str(exc.code)) from None
                time.sleep(attempt + 1)
            except urllib.error.URLError:
                raise RuntimeError("RPC connection failed; check BSC_RPC_URL") from None
        finished = UTC()
        raw = body.decode("utf-8")
        obj = json.loads(raw)
        if "error" in obj:
            err = obj["error"]
            raise RuntimeError("RPC method " + method + " returned code " + str(err.get("code")))
        if obj.get("id") != self.count or "result" not in obj:
            raise RuntimeError("malformed RPC response")
        self.records.append({"kind": kind, "method": method, "params": params,
                             "requested_utc_local": began, "received_utc_local": finished,
                             "raw_response_text": raw, "response_sha256": hashlib.sha256(body).hexdigest(),
                             "response_bytes": len(body)})
        return obj["result"]

    def transfers(self, wallet, ca, direction, prefix, per_page="0x8"):
        base = {"fromBlock": START, "toBlock": END, "category": ["erc20"],
                "contractAddresses": [ca], "order": "asc", "maxCount": per_page,
                ("toAddress" if direction == "in" else "fromAddress"): wallet}
        events, cursor, pages = [], None, 0
        while True:
            args = dict(base)
            if cursor:
                args["pageKey"] = cursor
            value = self.call(prefix + "_" + direction + "_PAGE_" + str(pages+1),
                              "alchemy_getAssetTransfers", [args])
            pages += 1
            if pages > 12 or not isinstance(value.get("transfers"), list):
                raise RuntimeError("unbounded or invalid transfer pagination")
            events.extend(value["transfers"])
            cursor = value.get("pageKey")
            if not cursor:
                return events, pages
            if len(events) >= 100:
                raise RuntimeError("unbounded transfer rows")

    def balanceof(self, wallet, ca, block, label):
        calldata = "0x70a08231" + wallet[2:].lower().rjust(64, "0")
        s = self.call(label, "eth_call", [{"to": ca, "data": calldata}, block])
        if not isinstance(s, str) or len(s) != 66 or not s.startswith("0x"):
            raise RuntimeError("balanceOf must return exact 32-byte uint256")
        return int(s, 16)

def raw_sum(rows):
    return sum(int(row["rawContract"]["value"], 16) for row in rows)

def collect(rpc):
    chain = rpc.call("CHAIN_ID", "eth_chainId", [])
    if int(chain, 16) != 56:
        raise RuntimeError("WRONG_CHAIN_ID expected BNB mainnet 0x38")
    summary = {"chain_id": chain, "source_limit": "tool/provider response only; not signed/attested"}
    token_in, inpages = rpc.transfers(W877, YOU, "in", "YOULI")
    token_out, outpages = rpc.transfers(W877, YOU, "out", "YOULI")
    owned = {
        "pre_first_buy": rpc.balanceof(W877, YOU, "0x793f51f", "YOULI_PRE_BUY"),
        "post_third_buy": rpc.balanceof(W877, YOU, "0x798b15d", "YOULI_POST_THIRD_BUY"),
        "post_last_sell": rpc.balanceof(W877, YOU, "0x7a5f44f", "YOULI_POST_LAST_SELL"),
        "cohort_end": rpc.balanceof(W877, YOU, END, "YOULI_COHORT_END"),
    }
    for i, h in enumerate(YOULI_BUYS):
        original = rpc.call("YOULI_BUY_" + str(i+1), "eth_getTransactionByHash", [h])
        if original["from"].lower() != W877 or original["hash"].lower() != h:
            raise RuntimeError("YOULI original owner BUY signer mismatch")
    unique_exits = sorted({x["hash"] for x in token_out})
    for h in unique_exits:
        original = rpc.call("YOULI_EXIT_" + h[2:10], "eth_getTransactionByHash", [h])
        if original["from"].lower() != W877:
            raise RuntimeError("YOULI original owner SELL signer mismatch")
    inflow, outflow = raw_sum(token_in), raw_sum(token_out)
    if (inflow != EXPECTED_YOULI["in"] or outflow != EXPECTED_YOULI["out"]
        or inflow - outflow != owned["cohort_end"]
        or owned["post_last_sell"] != owned["cohort_end"]
        or owned["pre_first_buy"] != 0 or inpages != 1 or outpages != 2
        or len(token_in) != 3 or len(token_out) != 14 or len(unique_exits) != 7):
        raise RuntimeError("YOULI frozen cohort evidence mismatch")
    summary["YOULI"] = {
        "in_pages": inpages, "out_pages": outpages, "in_rows": len(token_in),
        "out_rows": len(token_out), "unique_signed_exits": len(unique_exits),
        "raw_in": str(inflow), "raw_out": str(outflow), "raw_held": str(inflow-outflow),
        "token_balance_checkpoints": {k: str(v) for k,v in owned.items()},
        "state": "PARTIAL_TOKEN_EXIT; economic PnL UNRESOLVED",
    }
    all_ddac = []
    for case in ROUNDS:
        label, ca, buyblock, sellblock = (case[x] for x in
                                          ("label","ca","buy_block","sell_block"))
        into, p_in = rpc.transfers(WDD, ca, "in", label)
        out, p_out = rpc.transfers(WDD, ca, "out", label)
        balances = [
            rpc.balanceof(WDD, ca, hex(int(buyblock, 16)-1), label+"_PRE_BUY"),
            rpc.balanceof(WDD, ca, buyblock, label+"_POST_BUY"),
            rpc.balanceof(WDD, ca, sellblock, label+"_POST_SELL"),
            rpc.balanceof(WDD, ca, END, label+"_END"),
        ]
        block_values = []
        for phase, block in (("BUY",buyblock),("SELL",sellblock)):
            blk = rpc.call(label+"_"+phase+"_BLOCK", "eth_getBlockByNumber", [block,False])
            before = hex(int(block, 16)-1)
            cash_before = int(rpc.call(label+"_"+phase+"_BNB_PRE", "eth_getBalance", [WDD,before]),16)
            cash_after = int(rpc.call(label+"_"+phase+"_BNB_POST","eth_getBalance",[WDD,block]),16)
            nonce_before = int(rpc.call(label+"_"+phase+"_NONCE_PRE","eth_getTransactionCount",[WDD,before]),16)
            nonce_after = int(rpc.call(label+"_"+phase+"_NONCE_POST","eth_getTransactionCount",[WDD,block]),16)
            if blk["number"].lower() != block.lower():
                raise RuntimeError("DDAC block identity mismatch")
            block_values.append({"phase":phase,"block":block,"hash":blk["hash"],
                                 "native_before_wei":str(cash_before),
                                 "native_after_wei":str(cash_after),
                                 "native_delta_wei":str(cash_after-cash_before),
                                 "owner_nonce_delta":nonce_after-nonce_before})
        buy_pair = []
        for idx in case["buy_indices"]:
            tx = rpc.call(label+"_BUY_IDX_"+str(idx),"eth_getTransactionByBlockNumberAndIndex",
                          [buyblock,hex(idx)])
            receipt = rpc.call(label+"_BUY_RECEIPT_"+str(idx),
                               "eth_getTransactionReceipt",[tx["hash"]])
            if receipt["status"] != "0x1":
                raise RuntimeError("DDAC/leader failed BUY")
            buy_pair.append(tx)
        if (buy_pair[0]["from"].lower() != LEAD or buy_pair[1]["from"].lower() != WDD
                or buy_pair[0]["input"] != buy_pair[1]["input"]
                or buy_pair[0]["value"] != buy_pair[1]["value"]
                or buy_pair[1]["hash"].lower() != case["buy_hash"]
                or int(buy_pair[1]["value"],16) != 250000000000000000):
            raise RuntimeError("DDAC mirrored BUY evidence mismatch")
        sale_quartet=[]
        for idx in case["sell_indices"]:
            tx = rpc.call(label+"_SELL_IDX_"+str(idx),"eth_getTransactionByBlockNumberAndIndex",
                          [sellblock,hex(idx)])
            receipt = rpc.call(label+"_SELL_RECEIPT_"+str(idx),
                               "eth_getTransactionReceipt",[tx["hash"]])
            if receipt["status"] != "0x1":
                raise RuntimeError("DDAC/leader failed exit")
            sale_quartet.append(tx)
        if ([tx["from"].lower() for tx in sale_quartet] != [LEAD,LEAD,WDD,WDD]
            or [tx["input"][:10] for tx in sale_quartet] !=
                    ["0x095ea7b3","0x4d819a2a","0x095ea7b3","0x4d819a2a"]
            or sale_quartet[3]["hash"].lower() != case["sell_hash"]
            or p_in != 1 or p_out != 1 or raw_sum(into) != raw_sum(out)
            or balances != [0,raw_sum(into),0,0]
            or [x["owner_nonce_delta"] for x in block_values] != [1,2]):
            raise RuntimeError("DDAC mirrored exits/position/net transfer mismatch")
        all_ddac.append({"case":label,"token_ca":ca,"buy_hash":case["buy_hash"],
                         "sell_hash":case["sell_hash"],"token_raw_in_out":str(raw_sum(into)),
                         "token_balance_checkpoints":[str(x) for x in balances],
                         "block_native_accounting_not_pnl":block_values,
                         "mirrored_indices":{"buy":case["buy_indices"],
                                             "sell":case["sell_indices"]},
                         "economic_pnl":"UNRESOLVED"})
    summary["DDAC"] = all_ddac
    summary["gates"] = {"REALIZED_OWNER_NET_PNL":"UNRESOLVED",
                        "PUBLIC_EXECUTABLE_U":"UNRESOLVED","P5":"BLOCKED",
                        "PRODUCTION":"NO_GO"}
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Exclusive-create absolute or relative JSON evidence file")
    args = parser.parse_args()
    url = os.environ.get("BSC_RPC_URL")
    if not url:
        parser.error("set BSC_RPC_URL to an HTTPS Alchemy BNB Mainnet RPC endpoint (no secret printed)")
    rpc = ArchiveRPC(url)
    try:
        summary = collect(rpc)
    except Exception as exc:
        print("EVIDENCE_NOT_WRITTEN: " + str(exc).split("https://")[0][:190], file=sys.stderr)
        return 2
    document = {"schema":"BSC_P4B_VERBATIM_FIXED_877AF_DDAC_2026_10_19_V1",
                "created_utc_local":UTC(),
                "source_grade":"Raw JSON-RPC HTTP response bytes with local times and SHA256, NOT provider-signed and NOT independently attested",
                "network":"bnb-mainnet",
                "credential_policy":"RPC URL/API key never stored",
                "query_count":len(rpc.records),
                "raw_rpc_responses":rpc.records,
                "derived_read_only_summary":summary}
    result = json.dumps(document,ensure_ascii=False,indent=2)+"\n"
    output = Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    fd = os.open(str(output),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            handle.write(result)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        output.unlink(missing_ok=True)
        raise
    print("PASS read_only_source_captured", "queries="+str(len(rpc.records)),
          "source_sha256="+hashlib.sha256(result.encode()).hexdigest(),
          "output="+str(output))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
