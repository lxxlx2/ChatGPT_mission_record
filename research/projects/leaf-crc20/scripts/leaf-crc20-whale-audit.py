#!/usr/bin/env python3
import csv, json, time
import urllib.error, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

BASE="https://mempool.space/api"
WHALE="bc1pa8vrkzs2wrrh6nsu862vj50vgmsajtju5yv52atlm6xdf0nmaesqrffjrs"
PYLEAF="bc1phuuulh7fs5zrm48ethfyqvt860fxsaxuq643telqn06yz4u3c70spyleaf"
SATOSHI="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
OUT_REPORT=Path("leaf_crc20_whale_audit_report.json")
OUT_ACQ=Path("leaf_crc20_whale_acquisitions.csv")
OUT_SELLERS=Path("leaf_crc20_whale_sellers.csv")
OUT_CLUSTERS=Path("leaf_crc20_whale_clusters.json")
CACHE=Path("leaf_crc20_whale_tx_cache.json")
UA="leaf-crc20-whale-audit/1.0"

def http_get(url,tries=7,timeout=30):
    last=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
            last=e; wait=min(2**i,20); print(f"[retry {i+1}/{tries}] {url} -> {e}; sleep {wait}s"); time.sleep(wait)
    raise RuntimeError(f"GET failed: {url}: {last}")

def get_json(path): return json.loads(http_get(BASE+path).decode())

def extract_opreturn(h):
    try: b=bytes.fromhex(h)
    except Exception: return None
    if not b or b[0]!=0x6a: return None
    i=1
    if i>=len(b): return b""
    op=b[i]; i+=1
    if 1<=op<=75: ln=op
    elif op==0x4c:
        if i>=len(b): return None
        ln=b[i]; i+=1
    elif op==0x4d:
        if i+2>len(b): return None
        ln=int.from_bytes(b[i:i+2],"little"); i+=2
    else: return None
    return b[i:i+ln]

def leaf_amounts(tx):
    vals=[]
    for v in tx.get("vout",[]):
        d=extract_opreturn(v.get("scriptpubkey",""))
        if d is None: continue
        try: j=json.loads(d.decode())
        except Exception: continue
        if isinstance(j,dict) and str(j.get("p","")).lower()=="ico-20" and str(j.get("op","")).lower()=="transfer" and str(j.get("tick","")).upper()=="LEAF":
            try: vals.append(float(j.get("amt")))
            except Exception: pass
    return vals

def inv_by_addr(tx):
    d=defaultdict(int)
    for vin in tx.get("vin",[]):
        p=vin.get("prevout") or {}; a=p.get("scriptpubkey_address")
        if a: d[a]+=int(p.get("value") or 0)
    return d

def out_by_addr(tx):
    d=defaultdict(int)
    for v in tx.get("vout",[]):
        a=v.get("scriptpubkey_address")
        if a: d[a]+=int(v.get("value") or 0)
    return d

def address_history(addr):
    all_txs=[]; seen=set(); path=f"/address/{addr}/txs"; pages=0
    while True:
        batch=get_json(path)
        if not batch: break
        new=0
        for tx in batch:
            if tx["txid"] not in seen: seen.add(tx["txid"]); all_txs.append(tx); new+=1
        pages+=1; print(f"  page {pages}: returned={len(batch)} new={new} total={len(all_txs)}")
        confirmed=[x for x in batch if (x.get("status") or {}).get("confirmed")]
        if not confirmed or len(batch)<25: break
        path=f"/address/{addr}/txs/chain/{confirmed[-1]['txid']}"
        if pages>250: raise RuntimeError("pagination guard")
        time.sleep(.05)
    return all_txs

def load_cache():
    if CACHE.exists():
        try: return json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception: pass
    return {}

def save_cache(c): CACHE.write_text(json.dumps(c,ensure_ascii=False),encoding="utf-8")

def cached_tx(txid,c):
    if txid not in c:
        c[txid]=get_json(f"/tx/{txid}"); time.sleep(.05)
        if len(c)%25==0: save_cache(c)
    return c[txid]

class DSU:
    def __init__(self,xs): self.p={x:x for x in xs}
    def find(self,x):
        if self.p[x]!=x: self.p[x]=self.find(self.p[x])
        return self.p[x]
    def union(self,a,b):
        if a not in self.p or b not in self.p: return
        a,b=self.find(a),self.find(b)
        if a!=b: self.p[b]=a

def main():
    print("[1/6] whale history")
    txs=address_history(WHALE)
    raw=[]; freq=Counter()
    for tx in txs:
        amts=leaf_amounts(tx)
        if not amts: continue
        inv=inv_by_addr(tx)
        if WHALE not in inv: continue
        others=[a for a in inv if a!=WHALE]
        if not others: continue
        raw.append((tx,amts)); freq.update(set(others))
    print("candidate acquisition txs",len(raw))
    threshold=max(3,int(max(1,len(raw))*.10))
    recurring={a for a,n in freq.items() if n>=threshold}
    excluded=recurring|{WHALE,PYLEAF,SATOSHI}

    acquisitions=[]; sellers=set(); seller_sales=defaultdict(list); seller_prevouts=defaultdict(list)
    print("[2/6] economics")
    for tx,amts in raw:
        inv=inv_by_addr(tx); outv=out_by_addr(tx); nonwhale={a for a in inv if a!=WHALE}
        ss=sorted(a for a in nonwhale if a not in excluded and outv.get(a,0)>0)
        fallback=False
        if not ss: ss=sorted(a for a in nonwhale if a not in excluded); fallback=True
        seller_in=sum(inv.get(a,0) for a in ss); seller_out=sum(outv.get(a,0) for a in ss)
        whale_in=inv.get(WHALE,0); whale_out=outv.get(WHALE,0); st=tx.get("status") or {}
        row={"txid":tx["txid"],"block_height":st.get("block_height",""),"block_time":st.get("block_time",""),
             "leaf_amount":sum(amts),"leaf_transfer_count":len(amts),"seller_addresses":"|".join(ss),
             "seller_count":len(ss),"seller_heuristic_fallback":fallback,
             "seller_input_sats":seller_in,"seller_output_sats":seller_out,
             "seller_net_received_sats":seller_out-seller_in,"seller_net_received_btc":(seller_out-seller_in)/1e8,
             "whale_input_sats":whale_in,"whale_output_sats":whale_out,
             "whale_net_spend_sats":whale_in-whale_out,"whale_net_spend_btc":(whale_in-whale_out)/1e8,
             "tx_fee_sats":int(tx.get("fee") or 0),"non_whale_input_addresses":"|".join(sorted(nonwhale))}
        acquisitions.append(row)
        for s in ss:
            sellers.add(s); seller_sales[s].append(tx["txid"])
            for vin in tx.get("vin",[]):
                p=vin.get("prevout") or {}
                if p.get("scriptpubkey_address")==s:
                    seller_prevouts[s].append({"sale_txid":tx["txid"],"prev_txid":vin.get("txid"),"prev_vout":vin.get("vout"),"value":p.get("value")})
    print("unique inferred sellers",len(sellers))

    cache=load_cache()
    prev_ids=sorted({x["prev_txid"] for arr in seller_prevouts.values() for x in arr if x.get("prev_txid")})
    print("[3/6] seller UTXO parents",len(prev_ids))
    prevmap={}
    for i,t in enumerate(prev_ids,1):
        try: prevmap[t]=cached_tx(t,cache)
        except Exception as e: prevmap[t]={"_error":repr(e)}
        if i%25==0 or i==len(prev_ids): print(f"  {i}/{len(prev_ids)}")
    save_cache(cache)

    upstream=defaultdict(Counter); parent_to_sellers=defaultdict(set); source_to_sellers=defaultdict(set); seller_parents=defaultdict(set)
    print("[4/6] funding graph")
    for s,prevs in seller_prevouts.items():
        for item in prevs:
            txid=item["prev_txid"]; ptx=prevmap.get(txid,{})
            if "_error" in ptx: continue
            if not any(v.get("scriptpubkey_address")==s for v in ptx.get("vout",[])): continue
            seller_parents[s].add(txid); parent_to_sellers[txid].add(s)
            for vin in ptx.get("vin",[]):
                a=(vin.get("prevout") or {}).get("scriptpubkey_address")
                if not a or a==s: continue
                upstream[s][a]+=1; source_to_sellers[a].add(s)

    dsu=DSU(sorted(sellers)); edges=[]
    for txid,ss0 in parent_to_sellers.items():
        ss=sorted(ss0)
        if len(ss)>=2:
            for a in ss[1:]: dsu.union(ss[0],a)
            edges.append({"type":"common_parent_tx","evidence":txid,"sellers":ss})
    for src,ss0 in source_to_sellers.items():
        ss=sorted(ss0)
        if len(ss)>=2 and src not in excluded:
            for a in ss[1:]: dsu.union(ss[0],a)
            edges.append({"type":"common_upstream_address","evidence":src,"sellers":ss})
    clusters=defaultdict(list)
    for s in sorted(sellers): clusters[dsu.find(s)].append(s)
    multi=sorted([v for v in clusters.values() if len(v)>=2],key=lambda x:(-len(x),x[0]))

    seller_rows=[]
    for s in sorted(sellers):
        top=upstream.get(s,Counter()).most_common(10)
        seller_rows.append({"seller_address":s,"sale_tx_count":len(set(seller_sales[s])),
                            "sale_txids":"|".join(sorted(set(seller_sales[s]))),
                            "seller_input_utxo_count":len(seller_prevouts[s]),
                            "immediate_parent_tx_count":len(seller_parents[s]),
                            "immediate_parent_txids":"|".join(sorted(seller_parents[s])),
                            "top_upstream_sources":json.dumps(top,ensure_ascii=False),
                            "direct_protocol_related_upstream":any(a in recurring or a in {PYLEAF,WHALE} for a,_ in top)})

    print("[5/6] write")
    if acquisitions:
        with OUT_ACQ.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(acquisitions[0].keys())); w.writeheader(); w.writerows(sorted(acquisitions,key=lambda x:(x["block_height"],x["txid"])))
    if seller_rows:
        with OUT_SELLERS.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(seller_rows[0].keys())); w.writeheader(); w.writerows(seller_rows)
    clusters_out={"recurring_infrastructure_input_addresses":[{"address":a,"acquisition_tx_count":freq[a]} for a in sorted(recurring)],
                  "multi_seller_clusters":multi,"strong_edges":edges,
                  "common_parent_transactions":[{"txid":t,"sellers":sorted(ss),"seller_count":len(ss)} for t,ss in sorted(parent_to_sellers.items()) if len(ss)>=2],
                  "common_upstream_addresses":[{"address":a,"sellers":sorted(ss),"seller_count":len(ss),"is_recurring_trade_infrastructure":a in recurring} for a,ss in sorted(source_to_sellers.items()) if len(ss)>=2],
                  "method_note":"Immediate UTXO ancestry and common-funder heuristics indicate linkage, not proof of common beneficial ownership. Recurring trade-template addresses are separated from ownership evidence."}
    OUT_CLUSTERS.write_text(json.dumps(clusters_out,ensure_ascii=False,indent=2),encoding="utf-8")

    exact=sum(r["leaf_amount"] for r in acquisitions)
    sn=sum(r["seller_net_received_sats"] for r in acquisitions)
    wn=sum(r["whale_net_spend_sats"] for r in acquisitions)
    fees=sum(r["tx_fee_sats"] for r in acquisitions)
    report={"whale_address":WHALE,"address_history_tx_count":len(txs),"acquisition_tx_count":len(acquisitions),
            "unique_seller_address_count":len(sellers),"ico20_leaf_acquired_sum":exact,
            "seller_net_received_btc_sum":sn/1e8,"whale_net_spend_btc_sum":wn/1e8,"network_fee_btc_sum":fees/1e8,
            "recurring_infrastructure_input_addresses":[{"address":a,"acquisition_tx_count":freq[a]} for a in sorted(recurring)],
            "multi_seller_cluster_count":len(multi),"multi_seller_cluster_sizes":sorted([len(x) for x in multi],reverse=True),
            "sellers_with_direct_recurring_protocol_upstream":sum(bool(r["direct_protocol_related_upstream"]) for r in seller_rows),
            "claim_checks":{"claimed_acquisition_txs_149":len(acquisitions)==149,
                            "claimed_unique_sellers_120":len(sellers)==120,
                            "claimed_leaf_107813367_5647406":abs(exact-107813367.5647406)<1e-6,
                            "claimed_btc_0_605":{"seller_net_received_btc":sn/1e8,"whale_net_spend_btc":wn/1e8,
                                               "note":"The post may use a different cost convention. Both seller net receipts and whale net outflow are reported."}},
            "method_notes":["Acquisition requires whale input plus ICO-20 LEAF transfer plus at least one non-whale input.",
                            "Recurring non-whale input addresses are treated as protocol/coordinator infrastructure, not sellers.",
                            "Seller is inferred from non-infrastructure input address that also receives a positive output; fallbacks are flagged.",
                            "Seller net BTC equals outputs to inferred seller minus that seller's input sats.",
                            "Whale net BTC outflow equals whale input sats minus outputs returning to whale.",
                            "Immediate parent and common upstream address reuse are linkage heuristics, not proof of common ownership."]}
    OUT_REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("[6/6] done"); print(json.dumps(report,ensure_ascii=False,indent=2))
    for p in [OUT_REPORT,OUT_ACQ,OUT_SELLERS,OUT_CLUSTERS]: print(p)
if __name__=="__main__": main()
