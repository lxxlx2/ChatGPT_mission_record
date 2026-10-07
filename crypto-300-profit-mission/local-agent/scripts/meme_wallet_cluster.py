#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from mission_agent.meme.cluster import RpcCache, SolanaReadOnlyRPC, WalletClusterAnalyzer, load_registry, markdown


def main():
    parser=argparse.ArgumentParser(description="Free read-only Solana Meme wallet-cluster analysis")
    parser.add_argument("mint")
    parser.add_argument("--rpc",default=os.environ.get("SOLANA_RPC_URL","https://api.mainnet.solana.com"))
    parser.add_argument("--special-registry",default=str(Path(__file__).parents[1]/"config"/"meme_special_addresses.json"))
    parser.add_argument("--cache",default=str(Path.home()/".cache"/"mission-meme"/"wallet-cluster.sqlite"))
    parser.add_argument("--history-per-holder",type=int,default=30)
    parser.add_argument("--deep-holders",type=int,default=10)
    parser.add_argument("--funding-lookback",type=int,default=12)
    parser.add_argument("--material-pct",default="1")
    parser.add_argument("--output-dir")
    args=parser.parse_args()

    out=Path(args.output_dir) if args.output_dir else Path.cwd()/"wallet-cluster-output"/args.mint
    out.mkdir(parents=True,exist_ok=True)

    cache=RpcCache(Path(args.cache))
    try:
        rpc=SolanaReadOnlyRPC(args.rpc,cache=cache)
        registry=load_registry(Path(args.special_registry) if args.special_registry else None)
        report=WalletClusterAnalyzer(
            args.mint,
            rpc=rpc,
            special_registry=registry,
            history_per_holder=args.history_per_holder,
            deep_holders=args.deep_holders,
            funding_lookback=args.funding_lookback,
            material_pct=args.material_pct,
        ).analyze()
    finally:
        cache.close()

    stable=json.dumps(report,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    report["report_sha256"]=hashlib.sha256(stable).hexdigest()
    j=out/"cluster-report.json";m=out/"cluster-report.md"
    j.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
    m.write_text(markdown(report))
    print(json.dumps({
        "status":"OK",
        "mint":args.mint,
        "source":report["source"],
        "metrics":report["metrics"],
        "coverage":report["coverage"],
        "json":str(j),
        "markdown":str(m),
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
