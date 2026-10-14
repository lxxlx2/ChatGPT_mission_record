"""Exact-mint chain metadata, with explicit provenance and fail-closed reconciliation.

No URI/social fetch: on-chain labels are issuer supplied, not official endorsement.
"""
import base64
import hashlib
import json
import struct
import time

ALPHABET='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
METAPLEX='metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s'
TOKEN='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN22='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'

def decode_key(text):
    n=0
    for c in text:n=n*58+ALPHABET.index(c)
    raw=b'\0'*(len(text)-len(text.lstrip('1')))+(n.to_bytes((n.bit_length()+7)//8,'big') if n else b'')
    if len(raw)!=32:raise ValueError('INVALID_PUBKEY')
    return raw

def encode_key(raw):
    n=int.from_bytes(raw,'big');out=''
    while n:n,r=divmod(n,58);out=ALPHABET[r]+out
    return '1'*(len(raw)-len(raw.lstrip(b'\0')))+out

def _on_curve(raw):
    # Solana rejects any compressed Edwards point that decompresses, including torsion.
    p=2**255-19;y=int.from_bytes(raw,'little') & (2**255-1)
    if y>=p:return False
    d=(-121665*pow(121666,p-2,p))%p
    den=(d*y*y+1)%p
    if not den:return False
    x2=((y*y-1)*pow(den,p-2,p))%p
    return x2==0 or pow(x2,(p-1)//2,p)==1

def metadata_address(mint):
    program=decode_key(METAPLEX);key=decode_key(mint)
    for bump in range(255,-1,-1):
        raw=hashlib.sha256(b'metadata'+program+key+bytes([bump])+program+b'ProgramDerivedAddress').digest()
        if not _on_curve(raw):return encode_key(raw)
    raise ValueError('PDA_NOT_FOUND')

def _label(value):
    return value.rstrip('\0').strip() if isinstance(value,str) else None

def _record(state,mint,source,address,slot):
    if state.get('mint')!=mint:raise ValueError('METADATA_MINT_MISMATCH')
    if not all(isinstance(state.get(k),str) for k in ('name','symbol')):raise ValueError('METADATA_LABELS_INVALID')
    if 'updateAuthority' not in state:raise ValueError('UPDATE_AUTHORITY_MISSING')
    authority=state['updateAuthority']
    if authority is not None:decode_key(authority)
    return {'mint':mint,'name':_label(state['name']),'symbol':_label(state['symbol']),
            'update_authority':authority,'source':source,'account':address,'slot':slot,'commitment':'finalized'}

def _metaplex(value,mint,address,slot):
    if value.get('owner')!=METAPLEX:raise ValueError('METADATA_OWNER_MISMATCH')
    data=value.get('data')
    if not isinstance(data,list) or len(data)!=2 or data[1]!='base64':raise ValueError('METADATA_ENCODING_INVALID')
    raw=base64.b64decode(data[0],validate=True)
    if len(raw)<65 or raw[0]!=4:raise ValueError('NOT_METADATA_V1')
    state={'mint':encode_key(raw[33:65]),'updateAuthority':encode_key(raw[1:33])};offset=65
    for key,limit in (('name',32),('symbol',10),('uri',200)):
        if offset+4>len(raw):raise ValueError('METADATA_TRUNCATED')
        size=struct.unpack_from('<I',raw,offset)[0];offset+=4
        if size>limit or offset+size>len(raw):raise ValueError('METADATA_STRING_INVALID')
        state[key]=raw[offset:offset+size].decode('utf-8');offset+=size
    return _record(state,mint,'METAPLEX_METADATA',address,slot)

def read_metadata(mint,rpc,mint_result):
    records=[];attempts=[];blocking=False
    value=(mint_result or {}).get('value') or {};slot=((mint_result or {}).get('context') or {}).get('slot')
    if value.get('owner')==TOKEN22:
        parsed=((value.get('data') or {}).get('parsed') or {}) if isinstance(value.get('data'),dict) else {}
        extensions=(parsed.get('info') or {}).get('extensions') or []
        pointers=[x.get('state') or {} for x in extensions if isinstance(x,dict) and x.get('extension')=='metadataPointer']
        for ext in extensions:
            if not isinstance(ext,dict) or ext.get('extension')!='tokenMetadata':continue
            try:
                if len(pointers)!=1 or pointers[0].get('metadataAddress')!=mint:raise ValueError('SELF_METADATA_POINTER_UNCONFIRMED')
                records.append(_record(ext.get('state') or {},mint,'TOKEN2022_METADATA',mint,slot))
                attempts.append({'source':'TOKEN2022_METADATA','account':mint,'status':'VERIFIED','slot':slot})
            except (ValueError,TypeError) as exc:
                blocking=True;attempts.append({'source':'TOKEN2022_METADATA','account':mint,'status':'UNCONFIRMED','reason':str(exc)})
        for pointer in pointers:
            if pointer.get('metadataAddress') not in (None,mint):
                blocking=True;attempts.append({'source':'TOKEN2022_METADATA_POINTER','account':pointer.get('metadataAddress'),'status':'UNCONFIRMED','reason':'EXTERNAL_INTERFACE_NOT_SUPPORTED'})
    try:
        address=metadata_address(mint)
        result=rpc.call('getAccountInfo',[address,{'encoding':'base64','commitment':'finalized'}],ttl=60)
        account=(result or {}).get('value');meta_slot=((result or {}).get('context') or {}).get('slot')
        attempt={'source':'METAPLEX_METADATA','account':address,'slot':meta_slot}
        if account is None:attempt.update(status='MISSING',reason='ACCOUNT_NOT_FOUND')
        else:
            records.append(_metaplex(account,mint,address,meta_slot));attempt['status']='VERIFIED'
        attempts.append(attempt)
    except Exception as exc:
        blocking=True;attempts.append({'source':'METAPLEX_METADATA','status':'UNCONFIRMED','reason':str(exc) if isinstance(exc,ValueError) else type(exc).__name__})
    signatures={(r['name'],r['symbol'],r['update_authority']) for r in records}
    status='TOKEN_IDENTITY_CONFLICT' if len(signatures)>1 else ('VERIFIED' if records and not blocking else 'UNCONFIRMED')
    observed_at=time.time()
    for attempt in attempts:
        attempt.update(method='getAccountInfo',commitment='finalized',observed_at=observed_at)
    for record in records:
        record['observed_at']=observed_at
    return {'status':status,'records':records,'attempts':attempts,'observed_at':observed_at,
            'mint_response_sha256':hashlib.sha256(json.dumps(mint_result,sort_keys=True,separators=(',',':')).encode()).hexdigest()}

def reconcile_identity(mint,profile,market):
    metadata=profile.get('metadata') or {};chain=metadata.get('records') or []
    anchored=profile.get('mint')==mint and profile.get('status')=='OK' and profile.get('mint_account_status')=='VERIFIED'
    chain=[r for r in chain if r.get('mint')==mint] if anchored else []
    market_bound=market.get('mint')==mint and market.get('status')=='OK'
    markets=(market.get('identity_records') or []) if market_bound else []
    markets=[r for r in markets if r.get('mint')==mint]
    records=chain+markets
    labels={(_label(r.get('name')),_label(r.get('symbol'))) for r in records}
    conflict=metadata.get('status')=='TOKEN_IDENTITY_CONFLICT' or len(labels)>1
    verified=bool(chain) and anchored and metadata.get('status')=='VERIFIED'
    selected=chain[0] if verified and not conflict else None
    name=selected.get('name') if selected else None;symbol=selected.get('symbol') if selected else None
    display=' / '.join(x for i,x in enumerate((name,symbol)) if x and (i==0 or not name or x.casefold()!=name.casefold()))
    return {'mint':mint,'identity_status':'VERIFIED' if verified else 'UNCONFIRMED',
            'market_match_status':market.get('market_match_status','UNCONFIRMED') if market.get('mint')==mint else 'UNCONFIRMED',
            'conflict_status':'TOKEN_IDENTITY_CONFLICT' if conflict else ('NO_CONFLICT_OBSERVED' if verified and markets else 'UNCONFIRMED'),
            'name_display_status':'TOKEN_IDENTITY_CONFLICT' if conflict else ('CHAIN_METADATA' if selected else 'UNCONFIRMED'),
            'display_name':name,'display_symbol':symbol,'display_label':display or ('身份来源冲突' if conflict else '链上名称未确认'),
            'sources':records,'metadata_attempts':metadata.get('attempts') or [],'official_affiliation_status':'UNCONFIRMED','mint_account_reason':profile.get('reason')}
