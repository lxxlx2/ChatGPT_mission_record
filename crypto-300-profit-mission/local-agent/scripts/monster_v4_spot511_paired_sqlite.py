"""Research-only frozen Spot511 minute -> one global SQLite FIFO/Fair8 D0-D1 A/B.

No HTTP, orders, balances, notifications or deployment. Same Stage166 verified
minute tapes, same immutable D0 and D1 engine, only selection differs. The
24h quote proxy is NOT an archived exchange snapshot or point-in-time receipt.
"""
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sqlite3

import monster_v4_shadow as production
import monster_v4_spot511_closed_minute_feed as feed
import monster_v4_spot511_d0_d1_tape as tape_module
from monster_v4_445_stage162_first_valid_fair8_research import plan_eligible_eight

SCHEMA = 'MONSTER_SPOT511_GLOBAL_SQLITE_FIFO_FAIR8_RESEARCH_V1'
CAPACITY = 8
TICK_MS = 180000
FIVE_MS = 300000


def build_source_index(source_dir, db_path, *, asof_utc):
    """Only one 12960-minute tape in memory; stage verified source per symbol.

    db_path must not exist; index contains provenance and only wholly verified
    minute-derived data. The original publisher files remain untouched.
    """
    if not isinstance(asof_utc, datetime) or asof_utc.tzinfo is None or asof_utc.utcoffset() is None:
        raise ValueError('INDEX_ASOF_AWARE_UTC_REQUIRED')
    roster = feed.stage166.frozen_roster()
    if len(roster) != 511 or roster != sorted(set(roster)):
        raise ValueError('INDEX_FROZEN_511_DRIFT')
    dest = Path(db_path)
    if dest.exists() or dest.is_symlink():
        raise ValueError('INDEX_REFUSE_EXISTING_OUTPUT')
    dest.parent.mkdir(parents=True, exist_ok=True)
    # 'x' prevents overwrites even when two manual sessions race.
    fd = dest.open('xb')
    fd.close()
    db = sqlite3.connect(str(dest))
    try:
        db.executescript('''
            CREATE TABLE roster(symbol TEXT PRIMARY KEY);
            CREATE TABLE price_ticks(tick_ms INTEGER NOT NULL,symbol TEXT NOT NULL,
                price TEXT NOT NULL,quote24 TEXT NOT NULL,
                PRIMARY KEY(tick_ms,symbol));
            CREATE TABLE closed5(symbol TEXT NOT NULL,open_ms INTEGER NOT NULL,
                op TEXT NOT NULL,hi TEXT NOT NULL,lo TEXT NOT NULL,
                cl TEXT NOT NULL,volume TEXT NOT NULL,quote TEXT NOT NULL,
                PRIMARY KEY(symbol,open_ms));
            CREATE TABLE day_provenance(symbol TEXT NOT NULL,day TEXT NOT NULL,
                status TEXT NOT NULL,zip_sha256 TEXT,
                PRIMARY KEY(symbol,day));
            CREATE TABLE metadata(k TEXT PRIMARY KEY,v TEXT NOT NULL);
        ''')
        with db:
            db.executemany('INSERT INTO roster(symbol) VALUES(?)', [(s,) for s in roster])
            db.executemany('INSERT INTO metadata(k,v) VALUES(?,?)', [
                ('schema',SCHEMA),('frozen_population','511'),
                ('source_kind','OFFICIAL_PUBLISHER_1M_RECONSTRUCTED_PROXY'),
                ('asof_utc',asof_utc.astimezone(timezone.utc).isoformat()),
                ('original_historical_tick_receipt_PIT','UNPROVEN')])
        for symbol in roster:
            record = tape_module.VerifiedClosedMinuteTape(
                source_dir, symbol, asof_utc=asof_utc, roster=roster)
            proof = record.readiness()
            with db:
                db.executemany('INSERT INTO day_provenance VALUES(?,?,?,?)', [
                    (symbol,d,status,proof['publisher_zip_sha256'].get(d))
                    for d,status in proof['day_states'].items()])
                for tick in range(feed.START_MS,feed.END_MS,TICK_MS):
                    row=record.d0_at(tick)
                    if row is not None:
                        db.execute('INSERT INTO price_ticks VALUES(?,?,?,?)',
                            (tick,symbol,row['lastPrice'],row['quoteVolume']))
                # Each exact UTC 5m OHLC is materialized once, not six times
                # for every subsequent 3m poll. Never invent broken 5m bars.
                for idx in range(0,feed.TOTAL_MINUTES,5):
                    bars=record.minutes[idx:idx+5]
                    if len(bars)!=5 or any(b is None for b in bars):
                        continue
                    db.execute('INSERT INTO closed5 VALUES(?,?,?,?,?,?,?,?)',(
                        symbol,feed.EPOCH_MS+idx*feed.MINUTE_MS,
                        str(bars[0][0]),str(max(x[1] for x in bars)),
                        str(min(x[2] for x in bars)),str(bars[-1][3]),
                        str(sum((x[4] for x in bars),Decimal(0))),
                        str(sum((x[5] for x in bars),Decimal(0)))))
        with db:
            db.execute('INSERT INTO metadata(k,v) VALUES(?,?)',('completed','YES'))
    finally:
        db.close()
    return dest


def _source_roster(db):
    return [r[0] for r in db.execute('SELECT symbol FROM roster ORDER BY symbol')]


def _closed5_fetch(source_db, venue, symbol, tick):
    if venue != 'spot':
        raise ValueError('D1_NOT_SPOT_SOURCE')
    limit=(tick//FIVE_MS)*FIVE_MS
    rows=source_db.execute('''SELECT open_ms,op,hi,lo,cl,volume,quote
        FROM closed5 WHERE symbol=? AND open_ms<?
        ORDER BY open_ms DESC LIMIT 6''',(symbol,limit)).fetchall()
    rows.reverse()
    # Six consecutive but stale candles are not a valid current evaluation.
    # The last bar must be the most recently CLOSED UTC 5m bar at this tick.
    # Do not search backward past source outages and reuse old momentum.
    if (len(rows)!=6 or rows[-1][0]!=limit-FIVE_MS
            or any(rows[i+1][0]-rows[i][0]!=FIVE_MS for i in range(5))):
        raise ValueError('D1_MISSING_CURRENT_CONTIGUOUS_VERIFIED_5M')
    return [[r[0],r[1],r[2],r[3],r[4],r[5],r[0]+FIVE_MS-1,r[6]] for r in rows]


def _fair_process(db, tick, fetch):
    """Stage162's exact frozen eligible-eight planner, original D1 evaluator.

    Suppression touches only nonselected retry timestamps and is restored
    even on exceptions. It may never be confused with a production scheduler.
    """
    pending=[dict(r) for r in db.execute('''SELECT * FROM candidate_queue
        WHERE status='PENDING' AND retry_after_ms<=?
        ORDER BY first_seen_ms,id''',(tick,))]
    chosen=plan_eligible_eight(pending,tick,CAPACITY)
    keep={r['id'] for r in chosen}
    suppressed=[(r['id'],r['retry_after_ms']) for r in pending if r['id'] not in keep]
    try:
        if suppressed:
            with db:
                db.executemany('UPDATE candidate_queue SET retry_after_ms=? WHERE id=?',
                               [(tick+1,i) for i,_ in suppressed])
        result=production.process_queue(db,tick,fetch,limit=CAPACITY)
    finally:
        if suppressed:
            with db:
                db.executemany('UPDATE candidate_queue SET retry_after_ms=? WHERE id=?',
                               [(old,i) for i,old in suppressed])
            readback={r[0]:r[1] for r in db.execute(
                'SELECT id,retry_after_ms FROM candidate_queue WHERE id IN ('+
                ','.join('?' for _ in suppressed)+')',[x[0] for x in suppressed])}
            if readback!={i:old for i,old in suppressed}:
                raise RuntimeError('FAIR8_QUEUE_MASK_RESTORE_DRIFT')
    return result


def paired_replay(index_path, *, lane_dir=None, allow_synthetic_cohort=False):
    """Single global cross-symbol 3m poll; never stitch per-symbol queues.

    Never claims all 511 sources ready if source rows have censored slots.
    Synthetic smaller rosters are explicitly test-only with that result marked.
    """
    src=sqlite3.connect(f'file:{Path(index_path).resolve()}?mode=ro',uri=True)
    src.row_factory=sqlite3.Row
    lanes={}
    try:
        metadata=dict(src.execute('SELECT k,v FROM metadata'))
        if metadata.get('schema')!=SCHEMA or metadata.get('completed')!='YES':
            raise ValueError('INDEX_UNCOMMITTED_OR_WRONG_SCHEMA')
        roster=_source_roster(src)
        if (not roster or roster!=sorted(set(roster)) or
                (len(roster)!=511 and not allow_synthetic_cohort)):
            raise ValueError('INDEX_FROZEN_POPULATION_REQUIRED')
        if metadata.get('source_kind')!='OFFICIAL_PUBLISHER_1M_RECONSTRUCTED_PROXY':
            raise ValueError('INDEX_UNAPPROVED_SOURCE_KIND')
        if not allow_synthetic_cohort:
            if roster != feed.stage166.frozen_roster():
                raise ValueError('INDEX_ORIGINAL_T0_ROSTER_IDENTITY_DRIFT')
            count=src.execute('SELECT COUNT(*) FROM day_provenance').fetchone()[0]
            if count!=511*9:
                raise ValueError('INDEX_4599_PUBLISHER_DAY_CENSUS_DRIFT')
        if lane_dir is None:
            import tempfile
            temporary=tempfile.TemporaryDirectory(prefix='monster-spot511-paired-')
            directory=Path(temporary.name)
        else:
            temporary=None
            directory=Path(lane_dir)
            directory.mkdir(parents=True,exist_ok=True)
        try:
            for name in ('FIFO8','FAIR8'):
                path=directory/(name.lower()+'.sqlite')
                if path.exists() or path.is_symlink():
                    raise ValueError('PAIR_LANE_DB_OVERWRITE_REFUSED')
                lanes[name]=production.open_store(path)
            totals=Counter()
            lane_totals={name:Counter() for name in lanes}
            # Persistent per-episode observability only; no strategy state edits.
            first_selected={name:{} for name in lanes}
            first_evaluated={name:{} for name in lanes}
            for tick in range(feed.START_MS,feed.END_MS,TICK_MS):
                rows=src.execute('''SELECT symbol,price,quote24 FROM price_ticks
                    WHERE tick_ms=? ORDER BY symbol''',(tick,)).fetchall()
                if len(rows)>len(roster) or any(r['symbol'] not in roster for r in rows):
                    raise ValueError('SOURCE_GRID_OR_ROSTER_DRIFT')
                complete=len(rows)==len(roster)
                totals['ticks']+=1
                totals['ready_symbol_ticks']+=len(rows)
                totals['source_censored_symbol_ticks']+=len(roster)-len(rows)
                totals['full_d0_ticks' if complete else 'censored_d0_ticks']+=1
                if rows and not complete:
                    totals['partial_d0_ticks_scanned']+=1
                if not rows:
                    totals['zero_source_ticks']+=1
                def fetch(venue,symbol,now):
                    return _closed5_fetch(src,venue,symbol,now)
                for name,db in lanes.items():
                    # Preserve observable candidates during partial source failure.
                    # Never turn a missing symbol into an empty / zero signal,
                    # and never label partial input as a full-market poll.
                    if rows:
                        result=production.observe_snapshot(db,'spot',tick,[
                            {'symbol':r['symbol'],'lastPrice':r['price'],
                             'quoteVolume':r['quote24']} for r in rows])
                        lane_totals[name]['d0_new_watch']+=result['watch_new']
                        lane_totals[name]['d0_symbol_rows_scanned']+=len(rows)
                    if complete:
                        production.mark_source_health(db,'spot',tick)
                    else:
                        production.mark_source_health(db,'spot',tick,
                            f'REPLAY_PARTIAL_SPOT_POPULATION:{len(rows)}/{len(roster)}')
                    eligible=[dict(r) for r in db.execute('''SELECT id,venue,symbol,
                        first_seen_ms,deadline_ms,status,retry_after_ms,
                        last_evaluated_bar_ms FROM candidate_queue
                        WHERE status='PENDING' AND retry_after_ms<=?
                        ORDER BY first_seen_ms,id''',(tick,))]
                    chosen=(plan_eligible_eight(eligible,tick,CAPACITY)
                            if name=='FAIR8' else eligible[:CAPACITY])
                    prior={q['id']:q['last_evaluated_bar_ms'] for q in chosen}
                    outcome=(_fair_process(db,tick,fetch) if name=='FAIR8'
                             else production.process_queue(db,tick,fetch,limit=CAPACITY))
                    if outcome['selected']!=len(chosen):
                        raise RuntimeError('PAIR_SELECTED_IDS_OR_CAPACITY_DRIFT')
                    for q in chosen:
                        ident=q['id']
                        first_selected[name].setdefault(ident,tick)
                        row=db.execute('''SELECT last_evaluated_bar_ms FROM candidate_queue
                            WHERE id=?''',(ident,)).fetchone()
                        if row is None:
                            raise RuntimeError('PAIR_SELECTED_CANDIDATE_LOST')
                        after=row['last_evaluated_bar_ms']
                        before=prior[ident]
                        if (after is not None and
                                (before is None or after>before)):
                            first_evaluated[name].setdefault(ident,tick)
                    for k in ('completed','deferred','late','selected'):
                        lane_totals[name]['d1_'+k]+=outcome[k]
            if totals['ticks']!=3360:
                raise RuntimeError('PAIR_REPLAY_TICK_DRIFT')
            def events(db,kind):
                return {r[0]:r[1] for r in db.execute(
                    'SELECT event_id,observed_ms FROM events WHERE event_type=?',(kind,))}
            aw=events(lanes['FIFO8'],'WATCH_EARLY')
            bw=events(lanes['FAIR8'],'WATCH_EARLY')
            if aw!=bw:
                raise RuntimeError('PAIR_D0_WATCH_EVENT_OR_TIMESTAMP_DRIFT')
            a=events(lanes['FIFO8'],'SETUP_ACTIVE')
            b=events(lanes['FAIR8'],'SETUP_ACTIVE')
            def status_counts(db):
                return dict(db.execute('SELECT status,COUNT(*) FROM candidate_queue GROUP BY status'))
            def service_trace(name,db):
                episode=[]
                for row in db.execute('''SELECT id,venue,symbol,first_seen_ms,
                    deadline_ms,status FROM candidate_queue ORDER BY id'''):
                    ident=row['id']
                    selected=first_selected[name].get(ident)
                    evaluated=first_evaluated[name].get(ident)
                    episode.append({
                        'id':ident,'venue':row['venue'],'symbol':row['symbol'],
                        'first_seen_ms':row['first_seen_ms'],
                        'deadline_ms':row['deadline_ms'],
                        'status':row['status'],
                        'first_selected_ms':selected,'first_valid_eval_ms':evaluated,
                        'selected_before_deadline':selected is not None and
                            selected<=row['deadline_ms'],
                        'evaluated_before_deadline':evaluated is not None and
                            evaluated<=row['deadline_ms'],
                        'first_eval_delay_minutes':None if evaluated is None else
                            (evaluated-row['first_seen_ms'])/60000})
                return episode
            fifo_trace=service_trace('FIFO8',lanes['FIFO8'])
            fair_trace=service_trace('FAIR8',lanes['FAIR8'])
            def service_summary(episode):
                return {'watched_queue_episodes':len(episode),
                    'first_selected':sum(x['first_selected_ms'] is not None for x in episode),
                    'first_valid_5m_evaluated':sum(x['first_valid_eval_ms'] is not None for x in episode),
                    'selected_before_deadline':sum(x['selected_before_deadline'] for x in episode),
                    'evaluated_before_deadline':sum(x['evaluated_before_deadline'] for x in episode),
                    'never_selected':sum(x['first_selected_ms'] is None for x in episode),
                    'never_valid_evaluated':sum(x['first_valid_eval_ms'] is None for x in episode)}
            # Minute-derived tick coverage is NOT equivalent to all 4599
            # whole UTC archives having publisher SHA verification. The
            # first/last day can have unused minutes outside the tick grid.
            verified_whole_days = None
            if len(roster)==511 and not allow_synthetic_cohort:
                verified_whole_days=src.execute('''SELECT COUNT(*) FROM day_provenance
                    WHERE status='VERIFIED_FULL_DAY_1440'
                    AND zip_sha256 IS NOT NULL''').fetchone()[0]
            return {'schema':SCHEMA,'mode':'OFFLINE_SYNTHETIC_TEST' if allow_synthetic_cohort else 'OFFLINE_HISTORICAL_RESEARCH',
                'frozen_roster':len(roster),'ticks':totals['ticks'],
                'source_ready_symbol_ticks':totals['ready_symbol_ticks'],
                'source_censored_symbol_ticks':totals['source_censored_symbol_ticks'],
                'full_d0_ticks':totals['full_d0_ticks'],
                'censored_d0_ticks':totals['censored_d0_ticks'],
                'partial_d0_ticks_scanned':totals['partial_d0_ticks_scanned'],
                'zero_source_ticks':totals['zero_source_ticks'],
                'partial_d0_keeps_verified_symbols_not_full_market':True,
                'fifo':dict(lane_totals['FIFO8']), 'fair8':dict(lane_totals['FAIR8']),
                'fifo_queue_status':status_counts(lanes['FIFO8']),
                'fair8_queue_status':status_counts(lanes['FAIR8']),
                'fifo_first_service':service_summary(fifo_trace),
                'fair8_first_service':service_summary(fair_trace),
                'fifo_episodes':fifo_trace,'fair8_episodes':fair_trace,
                'same_d0_watch_id_and_time':aw==bw,'d0_watch_count':len(aw),
                'fifo_setups':len(a),'fair8_setups':len(b),
                'lost_setup_ids':sorted(a.keys()-b.keys()),
                'new_setup_ids':sorted(b.keys()-a.keys()),
                'shared_setup_time_changed_ids':sorted(k for k in a.keys()&b.keys() if a[k]!=b[k]),
                'verified_full_publisher_symbol_days':verified_whole_days,
                'required_full_publisher_symbol_days':511*9 if not allow_synthetic_cohort else None,
                'all_511_historical_sources_verified':(
                    not allow_synthetic_cohort and len(roster)==511 and verified_whole_days==511*9
                    and totals['censored_d0_ticks']==0),
                'first_seen_listing_pit_proven':False,
                'publisher_original_tick_available_at_proven':False,
                'd0_24h_quote_is_reconstructed_proxy_not_original_ticker':True,
                'net_executable_profit':'UNKNOWN','G0':'PARTIAL',
                'G1':'NOT_SCORABLE','G4':'UNKNOWN','G6':'NO_GO',
                'NO_DEPLOY':True,'NO_GMAIL':True,'NO_TRADES':True}
        finally:
            for db in lanes.values(): db.close()
            if temporary is not None:temporary.cleanup()
    finally:
        src.close()


def main():
    import argparse
    parser=argparse.ArgumentParser(description='Research-only Spot511 global paired SQLite replay')
    parser.add_argument('--source-dir',type=Path,required=True)
    parser.add_argument('--index',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--asof',type=lambda v:datetime.fromisoformat(v.replace('Z','+00:00')),required=True)
    parser.add_argument('--lane-dir',type=Path)
    args=parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError('PAIR_REFUSE_EXISTING_JSON_OUTPUT')
    build_source_index(args.source_dir,args.index,asof_utc=args.asof)
    report=paired_replay(args.index,lane_dir=args.lane_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as out:
        json.dump(report,out,sort_keys=True,indent=2,ensure_ascii=False)
        out.write('\n')
    print(json.dumps({'schema':report['schema'],'full_d0_ticks':report['full_d0_ticks'],
        'G6':report['G6'],'fifo_setups':report['fifo_setups'],
        'fair8_setups':report['fair8_setups']},sort_keys=True))

if __name__=='__main__':
    main()
