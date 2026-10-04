import copy
import gzip
import json
from pathlib import Path

import pytest
from mission_agent.signals.policy import load_policy, USDC
from mission_agent.signals.store import Ledger
from scripts.frank_v2_joint_oos_validation import (
    ACC,MULT,VARIANTS,BOUNDARY,compare,labels,run_model,read_raw,canonical_hash)
from test_frank_local_signals import active,put

POLICY=Path(__file__).parents[2]/'config/frank_local_signal_v1.json'


def signal(eid='one',typ=MULT,at=100,sig='buy'):
    return {'episode_id':eid,'signal_type':typ,'signal_id':eid+typ,
            'triggered_at':at,'triggering_signature':sig}


def test_equal_totals_preserve_replacement_identities():
    a={'signals':[signal('STONK')]};b={'signals':[signal('new-target')]}
    result=compare(a,b)
    assert [s['episode_id'] for s in result['new']]==['new-target']
    assert [s['episode_id'] for s in result['lost']]==['STONK']
    assert result['trigger_changes']==[]


def test_same_signal_time_and_signature_changes_are_not_new_identity():
    a={'signals':[signal()]};b={'signals':[signal(at=110,sig='later-buy')]}
    result=compare(a,b)
    assert not result['new'] and not result['lost']
    assert result['trigger_changes'][0]['delay_seconds']==10


def test_same_time_different_trigger_signature_is_reported():
    result=compare({'signals':[signal()]},{'signals':[signal(sig='other')]})
    assert result['trigger_changes'][0]['delay_seconds']==0


def test_joint_only_label_and_hft_loss_are_separate():
    models={n:{'ACC':None,'MULT':None,'hft_ever':False} for n in ('J0','J1','J2','J3')}
    models['J3']['MULT']=signal()
    assert labels({'models':models})==['COMPLEX_PLUS_ROLLING_NEW_SIGNAL']
    models['J0']['MULT']=signal();models['J1']['hft_ever']=True
    assert 'COMPLEX_REMOVES_SIGNAL_VIA_HFT' in labels({'models':models})


def test_frozen_recovery_values_no_new_variant():
    assert {v[2] for v in VARIANTS.values()}=={0,300,900}
    assert VARIANTS['J3']==(True,'ROLLING',0)


def test_raw_chain_binding_is_verified(tmp_path):
    p=tmp_path/'raw.gz';tx={'transaction':{'signatures':['real']}}
    p.write_bytes(gzip.compress(json.dumps(tx).encode()))
    assert read_raw(p,'real')==tx
    with pytest.raises(ValueError,match='RAW_SIGNATURE_BINDING'):read_raw(p,'other')


def test_oos_boundary_exact_timestamp():
    from datetime import datetime,timezone
    assert datetime.fromtimestamp(BOUNDARY,timezone.utc).isoformat()=='2026-09-30T09:39:20+00:00'


def test_complex_addition_creates_sticky_loss_and_rolling_recovers(tmp_path):
    source=Ledger(tmp_path/'input.sqlite');additions={}
    for i,at in enumerate((100000,100010,100020,102800,103000)):
        event=active('joint-'+str(i),100,13000);event['block_time']=at;event['slot']=at
        event['trade'].update(quote_asset=USDC,quote_amount_raw='13000000000',quote_decimals=6)
        if i in (1,2):
            additions[event['signature']]={'trade':copy.deepcopy(event['trade']),
                                            'evidence':copy.deepcopy(event['evidence'])}
            event.update(classification='UNKNOWN_NEEDS_REVIEW',trade=None)
        put(source,event)
    rows=source.db.execute('select * from signatures order by block_time,slot,signature').fetchall()
    original=[r['body'] for r in rows];policy=load_policy(POLICY)
    data={n:run_model(rows,additions,tmp_path/(n+'.sqlite'),policy,n) for n in ('J0','J1','J2','J3')}
    counts=lambda n:sum(s['signal_type']==MULT for s in data[n]['signals'])
    assert counts('J0')==1 and counts('J1')==0 and counts('J2')==1 and counts('J3')==1
    assert len(compare(data['J1'],data['J3'])['new'])==1
    assert data['J0']['ACTIVE_TRADE']==3 and data['J3']['ACTIVE_TRADE']==5
    assert [r['body'] for r in rows]==original
    assert canonical_hash(additions)==canonical_hash(copy.deepcopy(additions))


def test_nonfinite_raw_cannot_have_a_valid_hash():
    with pytest.raises(ValueError):canonical_hash({'amount':float('nan')})


@pytest.mark.parametrize('raw_present',[True,False])
def test_snapshot_raw_missing_fail_closed_and_boundary_excluded(tmp_path,raw_present):
    import sqlite3
    from scripts.frank_v2_joint_oos_validation import snapshot_oos
    from mission_agent.signals.classifier import classify
    from mission_agent.signals.engine import Engine
    from mission_agent.frank.rpc import WALLET
    from test_frank_fm import tx
    raw=tx();raw['blockTime']=BOUNDARY+1;raw['transaction']['signatures']=['oos']
    path=tmp_path/'oos.json.gz'
    if raw_present:path.write_bytes(gzip.compress(json.dumps(raw).encode()))
    source=Ledger(tmp_path/'source.sqlite');Engine(source,load_policy(POLICY))
    source.db.execute('CREATE TABLE signature_detections(signature TEXT)')
    source.db.execute('INSERT INTO signature_detections VALUES(?)',('oos',))
    event=classify('oos',raw,WALLET)
    source.db.execute('INSERT INTO signatures VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(
        WALLET,'oos','frank',raw['slot'],BOUNDARY+1,'original-seen','original-classified',canonical_hash(raw),str(path),json.dumps(event),'NO','research'))
    source.db.execute('INSERT INTO signatures VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(
        WALLET,'excluded','frank',raw['slot'],BOUNDARY,'old','old','missing','absent','{}','NO','research'))
    source.db.close()
    old=sqlite3.connect(tmp_path/'legacy.sqlite')
    old.executescript('CREATE TABLE frank_transactions(signature TEXT,slot INT,block_time INT,evidence_json TEXT); CREATE TABLE frank_observations(signature TEXT,detected_at TEXT,normalized_at TEXT);')
    old.close()
    rows,history=snapshot_oos(tmp_path/'source.sqlite',tmp_path/'legacy.sqlite',tmp_path/'target.sqlite',tmp_path)
    assert len(rows)==int(raw_present)
    assert history['raw_missing']==int(not raw_present)
    assert history['backfilled']==0
    assert history['durable_forward']==int(raw_present)
    assert all(r['signature']!='excluded' for r in rows)
