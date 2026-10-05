"""Synthetic fixtures exercise gate integrity; they are never live manual evidence."""
import gzip,hashlib,json
from pathlib import Path
import pytest
from scripts.frank_manual_gate import verify
from mission_agent.frank.collector import verify_acceptance
from mission_agent.frank.parser import normalize
from mission_agent.hashing import digest
from test_frank_fm import tx

@pytest.fixture
def packet(tmp_path):
    manual=tmp_path/'manual';raw=tmp_path/'raw500';processed=tmp_path/'processed'
    for path in [manual/'explorer',raw,processed/'normalized500']:path.mkdir(parents=True)
    reviews=[];evidence=[];audit=[]
    for i in range(500):
        sig=f'unit-fixture-{i:03}';t=tx();t['slot']=i+12;t['blockTime']+=i;e=normalize(sig,t);evidence.append(e)
        data=gzip.compress(json.dumps({'signature':sig,'status':'AVAILABLE','transaction':t}).encode());(raw/(sig+'.json.gz')).write_bytes(data);audit.append({'signature':sig,'raw_cache_sha256':hashlib.sha256(data).hexdigest()})
        (processed/'normalized500'/(sig+'.json.gz')).write_bytes(gzip.compress(json.dumps(e).encode()))
        if i<50:
            reviews.append({'signature':sig});name=f'{i}.txt';(manual/'explorer'/name).write_text('SYNTHETIC UNIT TEST FIXTURE')
            record={'signature':sig,'manual_label':'MANUAL_ACTIVE','review_complete':True,'explorer_evidence_files':[name],'wallet_is_signer':True,'wallet_is_fee_payer':True,'token_delta_exact_agreement':True,'signer_agreement':True,'authority_agreement':True}
            (manual/f'primary-{i+1:02}-review.json').write_text(json.dumps(record))
    (tmp_path/'independent-arithmetic-check500.json').write_text(json.dumps({'records':audit}))
    path=tmp_path/'packet.json';path.write_text(json.dumps({'sample':reviews}));fixed={'primary_packet_path':str(path),'primary_packet_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'primary50':reviews,'active_all13':[r['signature'] for r in reviews[:13]],'raw500_manifest_sha256':'fixture'}
    (processed/'review50-packet.json').write_bytes(path.read_bytes())
    (manual/'fixed-identity.json').write_text(json.dumps(fixed));(processed/'process500-summary.json').write_text(json.dumps({'parsed':500,'parser_errors':[],'evidence_hash':digest(evidence)}))
    return manual,raw,processed

def test_production_gate_rejects_caller_declared_counts():
    with pytest.raises(ValueError,match='ACCEPTANCE'):
        verify_acceptance({'processed':500,'manual_reviewed':50,'independent_explorer_review':True,'parser_errors':0})

def test_bound_review_and_same500_replay_pass(packet):
    assert verify(*packet)['FRANK_500_VALIDATED'] is True

@pytest.mark.parametrize('mutation,match',[
    ('packet','FIXED_PACKET_CHANGED'),('processed_packet','PROCESSED_PRIMARY_PACKET_CHANGED'),('raw','RAW500_BYTES_CHANGED'),('signer','SIGNER_BINDING'),('missing_capture','CAPTURE_MISSING'),('replay','FULL500_REPLAY_DRIFT')])
def test_gate_rejects_evidence_drift(packet,mutation,match):
    manual,raw,processed=packet
    if mutation=='packet':Path(json.loads((manual/'fixed-identity.json').read_text())['primary_packet_path']).write_text('changed')
    if mutation=='processed_packet':(processed/'review50-packet.json').write_text('changed')
    if mutation=='raw':(raw/'unit-fixture-100.json.gz').write_bytes(b'changed')
    if mutation=='signer':
        path=manual/'primary-01-review.json';r=json.loads(path.read_text());r['wallet_is_signer']=False;path.write_text(json.dumps(r))
    if mutation=='missing_capture':(manual/'explorer'/'0.txt').unlink()
    if mutation=='replay':
        path=processed/'normalized500'/'unit-fixture-100.json.gz';r=json.loads(gzip.decompress(path.read_bytes()));r['wallet_is_signer']=False;path.write_bytes(gzip.compress(json.dumps(r).encode()))
    with pytest.raises(ValueError,match=match):verify(*packet)
