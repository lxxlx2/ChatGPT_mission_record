import sqlite3

from mission_agent.mission_control.observations import ObservationStore


def setup():
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row;return db,ObservationStore(db)


def candidate():
    return {'person_id':'frank','mint':'Mint1','episode_id':'ep1','pattern':'MULTIPLE','runtime_status':'LIVE','latest_at':100,'latest_buy_at':100,'latest_side':'BUY','position_state':'OPEN'}


def result(price='1.02'):
    return {'decision':'BUY','metrics':{'execution_price_usdc':price,'frank_latest_buy_price_usdc':'1','price_deviation_pct':str((float(price)-1)*100),'price_impact_pct':'0.5'},'reasons':[],'missing':[]}


def quote(price='1.02'):
    return {'status':'OK','source':'JUPITER_OFFICIAL','input_usdc':'30','execution_price_usdc':price,'price_impact_pct':'0.5','route_exists':True,'observed_at':100}


def test_same_bucket_upserts_instead_of_growing():
    db,store=setup();store.record(candidate=candidate(),result=result('1.02'),quote=quote('1.02'),now=100,bucket_seconds=60);store.record(candidate=candidate(),result=result('1.05'),quote=quote('1.05'),now=119,bucket_seconds=60)
    assert db.execute('select count(*) from follow_observations').fetchone()[0]==1
    row=db.execute('select execution_price_usdc from follow_observations').fetchone();assert row[0]=='1.05'


def test_new_bucket_adds_one_forward_sample_and_prune_is_bounded():
    db,store=setup();store.record(candidate=candidate(),result=result(),quote=quote(),now=100,bucket_seconds=60);store.record(candidate=candidate(),result=result(),quote=quote(),now=180,bucket_seconds=60)
    assert db.execute('select count(*) from follow_observations').fetchone()[0]==2
    assert store.prune(1000,850)==1
    assert db.execute('select count(*) from follow_observations').fetchone()[0]==1
