import csv,json
from pathlib import Path
def json_file(path,value): Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def csv_file(path,rows,columns=None):
    columns=columns or sorted({k for r in rows for k in r}) or ['status']
    with Path(path).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for r in rows: writer.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()})
def report(out,person,availability,qualification,fixture_count,graph):
    text=f"# {person} offline historical validation\n\nEngineering execution: data collection / normalization / artifact generation completed; full pipeline acceptance remains INCOMPLETE. Test results are recorded separately.\n\nPERSON_PATTERN: OBSERVE_ONLY; production trading: NO_GO.\n\nResult: {qualification['status']}; strategy: NO_VALIDATED_PATTERN.\n\nRaw transactions cached: {availability['raw_transaction_count']}; complete history: {availability['history_complete']}. Valid fully reconstructed episodes: {qualification['valid_episode_count']}; executable replay coverage: 0. Source research fixture rows: {fixture_count} (excluded from qualification).\n\nWallet graph: {graph.status()}; accepted research wallets: {len(graph.accepted)}; unresolved identities: {len(graph.unresolved)}. Continuity remains unproved. A completeness percentage cannot be asserted without a known complete graph.\n\nBlocker: {availability['blocked_reason']}. Required credential options: SOLANA_RPC_URL / ALCHEMY_API_KEY / HELIUS_API_KEY. Historical executable quote input: HISTORICAL_QUOTES_FILE. No key value or endpoint is persisted.\n\nCheckpoint: raw-events.sqlite, checkpoints table. Resume: python3 -m meme_person_validation validate --person {person} --max-pages 100\n\nNo thresholds learned from source research; no holdout consumed; no research qualification. Raw balance deltas are UNKNOWN until a verified user-route decoder and economic reconciliation are available.\n"
    (out/'validation-report.md').write_text(text)
