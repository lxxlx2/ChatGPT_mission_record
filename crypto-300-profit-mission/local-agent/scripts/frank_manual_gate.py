"""Bind fixed human review records to the same immutable 500-transaction replay."""
import argparse,gzip,hashlib,json
from pathlib import Path
from collections import Counter
from mission_agent.frank.parser import normalize,PARSER_VERSION
from mission_agent.hashing import digest,canonical
from mission_agent.frank.archive import publish
LABELS={'MANUAL_ACTIVE':'ACTIVE_SWAP_LIKE','MANUAL_PASSIVE':'PASSIVE_RECEIPT_LIKE','MANUAL_TRANSFER_OUT':'TRANSFER_OUT_LIKE','MANUAL_TRANSFER_IN':'TRANSFER_IN_LIKE','MANUAL_UNKNOWN':'UNKNOWN','MANUAL_FAILED':'FAILED','MANUAL_LP':'LP_LIKE','MANUAL_STAKE':'STAKE_LIKE'}
def verify(manual,raw,processed):
    fixed=json.loads((manual/'fixed-identity.json').read_text())
    audit=json.loads((raw.parent/'independent-arithmetic-check500.json').read_text())
    hashes={r['signature']+'.json.gz':r['raw_cache_sha256'] for r in audit['records']}
    if len(hashes)!=500 or set(hashes)!={p.name for p in raw.glob('*.json.gz')}:raise ValueError('RAW500_FIXED_IDENTITY_CHANGED')
    for name,sha in hashes.items():
        if hashlib.sha256((raw/name).read_bytes()).hexdigest()!=sha:raise ValueError('RAW500_BYTES_CHANGED')
    packet=Path(fixed['primary_packet_path'])
    if hashlib.sha256(packet.read_bytes()).hexdigest()!=fixed['primary_packet_sha256']:raise ValueError('FIXED_PACKET_CHANGED')
    if (processed/'review50-packet.json').read_bytes()!=packet.read_bytes():raise ValueError('PROCESSED_PRIMARY_PACKET_CHANGED')
    records=[json.loads((manual/f'primary-{i:02}-review.json').read_text()) for i in range(1,51)]
    if [r['signature'] for r in records]!=[r['signature'] for r in fixed['primary50']]:raise ValueError('PRIMARY_IDENTITY_CHANGED')
    extras=[json.loads(p.read_text()) for p in sorted(manual.glob('active-extra-*-review.json'))]
    by_sig={r['signature']:r for r in records+extras}
    axes=Counter();confusion=Counter();false_active=0;reviews=[]
    for r in records+extras:
        if r.get('review_complete') is not True:raise ValueError('REVIEW_INCOMPLETE')
        captures=r.get('explorer_evidence_files',r.get('explorer_capture_files',[]))
        if not captures:raise ValueError('INDEPENDENT_EVIDENCE_MISSING')
        for name in captures:
            path=manual/'explorer'/name
            if not path.is_file() or not path.stat().st_size:raise ValueError('EXPLORER_CAPTURE_MISSING:'+name)
        sig=r['signature'];record=json.loads(gzip.decompress((raw/(sig+'.json.gz')).read_bytes()))
        e=normalize(sig,record['transaction']);stored=json.loads(gzip.decompress((processed/'normalized500'/(sig+'.json.gz')).read_bytes()))
        if e!=stored:raise ValueError('REPLAY_PARSER_DRIFT')
        if r['wallet_is_signer']!=e['wallet_is_signer'] or r['wallet_is_fee_payer']!=e['wallet_is_fee_payer']:raise ValueError('REVIEW_SIGNER_BINDING_MISMATCH')
        expected_deltas=r.get('canonical_owned_deltas',r.get('canonical_owned_token_deltas'))
        if expected_deltas is not None and expected_deltas!=[d for d in e['token_balance_deltas'] if d['wallet_owned'] and (int(d['delta']) or not any(int(x['delta']) for x in e['token_balance_deltas'] if x['wallet_owned']))]:
            # Some reviews retain all owned accounts, including unchanged intermediate mints.
            if expected_deltas!=[d for d in e['token_balance_deltas'] if d['wallet_owned']]:raise ValueError('REVIEW_TOKEN_BINDING_MISMATCH')
        expected_auth=r.get('canonical_authorities',r.get('canonical_authority_records'))
        if expected_auth is not None and expected_auth!=[x for x in e['authority_accounts'] if x['matches_wallet']]:raise ValueError('REVIEW_AUTHORITY_BINDING_MISMATCH')
        label=LABELS.get(r['manual_label'],r['manual_label']);actual=e['mechanical_classification']
        if actual=='ACTIVE_SWAP_LIKE' and label!=actual:false_active+=1
        if r in records:
            confusion[(label,actual)]+=1
            axes['classification']+=label==actual
            axes['token_delta']+=r.get('token_delta_exact_agreement') is True
            axes['signer']+=r.get('signer_agreement',r.get('signer_fee_payer_agreement')) is True
            axes['authority']+=r.get('authority_agreement') is True
        reviews.append({'signature':sig,'record_sha256':hashlib.sha256(canonical(r)).hexdigest(),'evidence_sha256':e['evidence_sha256']})
    active=fixed['active_all13']
    active_final={s:normalize(s,json.loads(gzip.decompress((raw/(s+'.json.gz')).read_bytes()))['transaction'])['mechanical_classification'] for s in active}
    if any(label!='ACTIVE_SWAP_LIKE' for label in active_final.values()):raise ValueError('ACTIVE13_FINAL_FALSE_NEGATIVE')
    if len(active)!=13 or any(s not in by_sig or LABELS.get(by_sig[s]['manual_label'],by_sig[s]['manual_label'])!='ACTIVE_SWAP_LIKE' for s in active):raise ValueError('ACTIVE13_INCOMPLETE')
    summary=json.loads((processed/'process500-summary.json').read_text())
    replay=[]
    for path in sorted(raw.glob('*.json.gz')):
        record=json.loads(gzip.decompress(path.read_bytes()))
        if record['status']!='AVAILABLE':raise ValueError('RAW500_UNAVAILABLE')
        e=normalize(record['signature'],record['transaction']);saved=json.loads(gzip.decompress((processed/'normalized500'/path.name).read_bytes()))
        if e!=saved:raise ValueError('FULL500_REPLAY_DRIFT')
        replay.append(e)
    replay.sort(key=lambda e:(e['block_time'],e['slot'],e['signature']))
    if len(replay)!=500 or digest(replay)!=summary['evidence_hash']:raise ValueError('FULL500_HASH_MISMATCH')
    passed=summary['parsed']==500 and not summary['parser_errors'] and axes['classification']>=48 and axes['token_delta']==50 and axes['signer']==50 and axes['authority']>=49 and false_active==0
    return {'FRANK_500_VALIDATED':passed,'parser_version':PARSER_VERSION,'primary_packet_sha256':fixed['primary_packet_sha256'],'raw_manifest_sha256':fixed['raw500_manifest_sha256'],'processed_evidence_hash':summary['evidence_hash'],'primary50_axes':dict(axes),'primary50_confusion':[{'manual':a,'parser':b,'count':n} for (a,b),n in sorted(confusion.items())],'active13_reviewed':13,'active_false_positives':false_active,'reviews':reviews}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manual',type=Path,required=True);p.add_argument('--raw',type=Path,required=True);p.add_argument('--processed',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=verify(a.manual,a.raw,a.processed);publish(a.output,canonical(r));print(json.dumps({k:v for k,v in r.items() if k!='reviews'}));raise SystemExit(0 if r['FRANK_500_VALIDATED'] else 1)
