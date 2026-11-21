"""Pump.fun launch identity, creator metadata/post chain and second-provider parity (injected I/O)."""
import base64,hashlib
import pytest
from mission_agent.meme.holder_ranks import find_program_address,b58decode32,_b58,on_ed25519_curve
from mission_agent.meme.launch_identity import collect_pump_launch,collect_token_metadata,PUMP_PROGRAM,BONDING_CURVE_DISCRIMINATOR
from mission_agent.meme.narrative import collect_origin,ipfs_candidates
from mission_agent.meme.independent_check import collect_independent_balance_check

MINT='BXoHJddsWJLHtAopeiSbKUSELsu8hSFMs8baGMDkpump'
CREATOR='Fk6aSJfML6bxQcCXkyVpu898sgB5ZjgNUTcX3jzXywqa'


def test_pump_bonding_curve_pda_matches_chain_address():
    addr,bump=find_program_address([b'bonding-curve',b58decode32(MINT)],PUMP_PROGRAM)
    assert addr=='F1pP9NasikBnCse6SRujA3fEokC8LBpNjYjnGvANgscL' and bump==255 and on_ed25519_curve(addr) is False


class One:
    def __init__(self,value):self.value=value;self.calls=[]
    def call(self,method,params,ttl=0):
        self.calls.append((method,params[0]));return {'context':{'slot':7},'value':self.value}


def curve_account(owner=PUMP_PROGRAM,disc=BONDING_CURVE_DISCRIMINATOR):
    b=bytearray(disc+bytes(40)+b'\x01'+b58decode32(CREATOR)+bytes(10))
    return {'owner':owner,'data':[base64.b64encode(bytes(b)).decode(),'base64'],'executable':False}


def test_pump_launch_decodes_creator_and_registers_roles():
    out=collect_pump_launch(MINT,One(curve_account()))
    assert out['status']=='VERIFIED_CHAIN_STATE' and out['creator']==CREATOR and out['complete'] is True
    assert collect_pump_launch(MINT,One(None))['status']=='NOT_PUMP_LAUNCH'
    assert collect_pump_launch(MINT,One(curve_account(owner='11111111111111111111111111111111')))['status']=='NOT_PUMP_LAUNCH'
    assert collect_pump_launch(MINT,One(curve_account(disc=bytes(8))))['reason']=='BONDING_CURVE_LAYOUT_MISMATCH'


def test_token2022_metadata_extension_needs_no_extra_read():
    rpc=One(None)
    out=collect_token_metadata(MINT,{'token_metadata':{'uri':'https://x.example/a.json','name':'N','symbol':'S','update_authority':None}},rpc)
    assert out['status']=='VERIFIED_CHAIN_STATE' and out['is_mutable'] is False and rpc.calls==[]


def test_ipfs_gateway_candidates_preserve_cid():
    c=ipfs_candidates('https://ipfs.io/ipfs/bafkreiae3diu6wznn2vmmojusoq4iam6fdfrql4lswueqbzefocm5qhkmy')
    assert len(c)==3 and all('bafkreiae3diu6wznn2vmmojusoq4iam6fdfrql4lswueqbzefocm5qhkmy' in x for x in c)
    assert ipfs_candidates('javascript:alert(1)')==[]


def tweet(user,tid,ts,text,quote=None):
    return {'url':f'https://x.com/{user}/status/{tid}','id':tid,'text':text,'created_timestamp':ts,
            'author':{'screen_name':user,'id':'10','followers':10,'verification':{'verified':True,'type':'individual'}},'quote':quote}


def test_origin_separates_creator_link_from_author_confirmation_and_follows_quote():
    q=tweet('orig','11111',100,'Web crawlers')
    pages={'https://a.ipfs.4everland.io':None}
    def fetch(url):
        if 'ipfs' in url:return {'status':'OK','json':{'name':'CRAWLNET','symbol':'CRAWL','twitter':'https://x.com/dev/status/22222'},'response_sha256':'0'*64}
        if url.endswith('/dev/status/22222'):return {'status':'OK','json':{'tweet':tweet('dev','22222',200,'i built it',q)},'response_sha256':'1'*64}
        if url.endswith('/orig/status/11111'):return {'status':'OK','json':{'tweet':q},'response_sha256':'2'*64}
        return {'status':'UNAVAILABLE','reason':'HTTP_404'}
    md={'status':'VERIFIED_CHAIN_STATE','mint':MINT,'uri':'ipfs://bafkreiae3diu6wznn2vmmojusoq4iam6fdfrql4lswueqbzefocm5qhkmy','name':'CRAWLNET','symbol':'CRAWL','is_mutable':False}
    out=collect_origin(MINT,md,{'main_pair':{'pair_created_at_ms':298000}},fetch_json=fetch,clock=lambda:1)
    assert out['ca_link_status']=='CREATOR_METADATA_LINKS_POST'
    assert [p['author'] for p in out['posts']]==['dev','orig'] and out['posts'][1]['quoted_by'].endswith('/22222')
    assert out['earliest_traceable']['author']=='orig' and out['linked_post_to_pair_seconds']==98.0
    assert not any(p['exact_ca_mentioned'] for p in out['posts'])


@pytest.mark.parametrize('mint,case,expected',[
    ('111111111111111111111111111111JF','claim','EXACT_CA_CLAIM_VERIFIED'),
    ('111111111111111111111111111111JG','other_mint','LINK_ONLY'),
    ('111111111111111111111111111111JH','wrong_author','LINK_ONLY'),
    ('111111111111111111111111111111JJ','no_source','SOURCE_UNAVAILABLE'),
])
def test_origin_distinguishes_mentions_claims_and_source_failure_across_mints(mint,case,expected):
    authority_link='https://x.com/issuer/status/22345'
    meta={'status':'VERIFIED_CHAIN_STATE','mint':mint,'uri':'https://project.example/meta.json'}
    author='imposter' if case=='wrong_author' else 'issuer'
    address=MINT if case=='other_mint' else mint
    ancestor=tweet('source','12345',100,'A different story')
    issuer=tweet(author,'22345',200,'Our official CA: '+address,quote=ancestor)
    issuer.update(replying_to='source',replying_to_status='12345')
    calls=[]
    def fetch(url):
        calls.append(url)
        if case=='no_source':return {'status':'UNAVAILABLE','reason':'HTTP_403'}
        if url==meta['uri']:data={'twitter':authority_link}
        elif url.endswith('/22345'):data={'tweet':issuer}
        else:data={'tweet':ancestor}
        return {'status':'OK','json':data,'response_sha256':'a'*64}
    out=collect_origin(mint,meta,{'narrative_post_links':[authority_link]},fetch_json=fetch)
    assert out['recognition']['status']==expected
    if case=='claim':
        assert [edge['type'] for edge in out['interactions']]==['QUOTE','REPLY']
        assert sum(url.endswith('/12345') for url in calls)==1
    if case=='wrong_author':
        assert out['posts']==[] and any(r['reason']=='POST_LINK_AUTHOR_MISMATCH' for r in out['unresolved_links'])


def test_origin_without_metadata_is_unavailable_not_invented():
    out=collect_origin(MINT,None,{},fetch_json=lambda u:{'status':'UNAVAILABLE'},clock=lambda:1)
    assert out['status']=='UNAVAILABLE' and out['ca_link_status']=='UNVERIFIED' and out['posts']==[]


class Parsed:
    def __init__(self,slot,amounts):self.slot=slot;self.amounts=amounts
    def call(self,method,params,ttl=0):
        vals=[]
        for a in params[0]:
            if a==MINT:vals.append({'data':{'parsed':{'info':{'supply':'100'}}}})
            elif a in self.amounts:vals.append({'data':{'parsed':{'info':{'tokenAmount':{'amount':self.amounts[a]},'owner':'o','mint':MINT}}}})
            else:vals.append(None)
        return {'context':{'slot':self.slot},'value':vals}


def test_independent_check_reports_slot_relation_and_differences():
    acct=CREATOR
    same=collect_independent_balance_check(MINT,[acct],Parsed(5,{acct:'60'}),Parsed(5,{acct:'60'}),clock=lambda:0)
    assert same['status']=='SAME_SLOT_ALL_MATCH' and same['matches']==2
    near=collect_independent_balance_check(MINT,[acct],Parsed(5,{acct:'60'}),Parsed(6,{acct:'61'}),clock=lambda:0)
    assert near['status']=='NEAR_TIME_DIFFERENCES' and near['rows'][1]['difference_raw']=='1'
    assert collect_independent_balance_check(MINT,[acct],Parsed(5,{}),None)['status']=='NOT_REQUESTED'
