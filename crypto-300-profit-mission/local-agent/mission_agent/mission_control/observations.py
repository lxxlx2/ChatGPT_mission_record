"""Bounded forward evidence for follow-policy calibration."""
from __future__ import annotations

import json
from ..hashing import digest


class ObservationStore:
    def __init__(self,db):
        self.db=db
        self.db.execute('''CREATE TABLE IF NOT EXISTS follow_observations(
            observation_id TEXT PRIMARY KEY,
            entity_key TEXT NOT NULL,
            person_id TEXT NOT NULL,
            mint TEXT NOT NULL,
            episode_id TEXT,
            bucket_start INTEGER NOT NULL,
            observed_at REAL NOT NULL,
            pattern TEXT,
            decision TEXT NOT NULL,
            runtime_status TEXT,
            execution_price_usdc TEXT,
            frank_latest_buy_price_usdc TEXT,
            price_deviation_pct TEXT,
            price_impact_pct TEXT,
            route_exists INTEGER,
            body TEXT NOT NULL,
            UNIQUE(entity_key,bucket_start)
        )''')
        self.db.execute('CREATE INDEX IF NOT EXISTS idx_follow_observations_entity_time ON follow_observations(entity_key,bucket_start)')

    @staticmethod
    def entity_key(candidate):
        return digest({'person_id':candidate.get('person_id'),'mint':candidate.get('mint'),'episode_id':candidate.get('episode_id')})

    def record(self,*,candidate,result,quote,now,bucket_seconds=60):
        bucket=int(now)//int(bucket_seconds)*int(bucket_seconds);entity=self.entity_key(candidate);metrics=result.get('metrics') or {}
        body={'candidate':{k:candidate.get(k) for k in ('person_id','mint','episode_id','pattern','runtime_status','latest_at','latest_buy_at','latest_side','position_state')},'decision':result.get('decision'),'metrics':metrics,'reasons':result.get('reasons') or [],'missing':result.get('missing') or [],'quote':{k:quote.get(k) for k in ('status','reason','source','input_usdc','execution_price_usdc','price_impact_pct','route_exists','observed_at')}}
        observation_id=digest({'entity_key':entity,'bucket_start':bucket});encoded=json.dumps(body,sort_keys=True)
        self.db.execute('''INSERT INTO follow_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(entity_key,bucket_start) DO UPDATE SET observed_at=excluded.observed_at,decision=excluded.decision,runtime_status=excluded.runtime_status,execution_price_usdc=excluded.execution_price_usdc,frank_latest_buy_price_usdc=excluded.frank_latest_buy_price_usdc,price_deviation_pct=excluded.price_deviation_pct,price_impact_pct=excluded.price_impact_pct,route_exists=excluded.route_exists,body=excluded.body''',
            (observation_id,entity,candidate.get('person_id'),candidate.get('mint'),candidate.get('episode_id'),bucket,float(now),candidate.get('pattern'),result.get('decision'),candidate.get('runtime_status'),metrics.get('execution_price_usdc'),metrics.get('frank_latest_buy_price_usdc'),metrics.get('price_deviation_pct'),metrics.get('price_impact_pct'),None if quote.get('route_exists') is None else int(bool(quote.get('route_exists'))),encoded))
        return observation_id

    def prune(self,now,retention_seconds):
        cutoff=int(now)-int(retention_seconds);return self.db.execute('DELETE FROM follow_observations WHERE bucket_start<?',(cutoff,)).rowcount
