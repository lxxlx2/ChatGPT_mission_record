"""Public narrative is bounded source claims, never inferred CA endorsement."""
import base64
import json
import socket
import subprocess
import types
import pytest
from mission_agent.meme import public_html
from mission_agent.meme.narrative import PublicNarrativeClient,extract_page_claim
from test_meme_holder_ranks import MINT,key

URL='https://project.example.org/about'


def html(description=None,body='',extra=''):
    return ('<html lang="en"><head><title>Fixture project story</title><meta name="author" content="Fixture Team">'
            '<meta name="description" content="'+(description or 'A community story about a fictional cat exploring distant planets.')+'">'+extra+'</head><body>'+body+'</body></html>').encode()


def test_page_claim_and_exact_ca_are_separate_from_official_recognition():
    row=extract_page_claim(html(body='Contract: '+MINT),URL,MINT,100)
    assert row['classification']=='THIRD_PARTY_CLAIM'
    assert row['exact_ca_mentioned'] is True
    assert row['official_recognition']=='UNVERIFIED'
    assert row['published_at_claim'] is None and row['first_seen_at']==100
    assert len(row['excerpt'].split())<=16
    assert len(row['response_sha256'])==64


def test_narrative_still_exists_without_exact_ca_mention():
    row=extract_page_claim(html(),URL,MINT,100)
    assert row['excerpt'] and row['exact_ca_mentioned'] is False
    assert row['official_recognition']=='UNVERIFIED'


def test_ca_in_url_scripts_or_longer_identifier_is_not_a_content_mention():
    value=html(body='<script>const ca="'+MINT+'"</script>1'+MINT+'2')
    row=extract_page_claim(value,'https://pump.fun/coin/'+MINT,MINT,100)
    assert row['url_contains_ca'] is True and row['exact_ca_mentioned'] is False


@pytest.mark.parametrize('date',['2026-11-01T12:00:00Z','2026-11-01T19:00:00+07:00'])
def test_publisher_date_is_a_separate_timezone_aware_claim(date):
    row=extract_page_claim(html(extra='<meta property="article:published_time" content="'+date+'">'),URL,MINT,100)
    assert row['published_at_claim']=='2026-11-01T12:00:00+00:00'
    assert row['first_seen_at']==100


@pytest.mark.parametrize('date',['2026-11-01','yesterday','2026-11-01T12:00:00'])
def test_unknown_publication_time_is_not_replaced_by_retrieval_time(date):
    row=extract_page_claim(html(extra='<meta property="article:published_time" content="'+date+'">'),URL,MINT,100)
    assert row['published_at_claim'] is None


@pytest.mark.parametrize('page',[b'<html><title>Just a moment...</title><body>Verify you are human</body></html>',b'<html><title>Log in to X</title></html>',b'<html><script>narrative="secret"</script></html>'])
def test_access_wall_or_script_only_page_does_not_invent_posts(page):
    with pytest.raises(ValueError):extract_page_claim(page,URL,MINT,100)


@pytest.mark.parametrize('url',['http://project.example.org/','https://user:pass@project.example.org/','https://localhost/','https://127.0.0.1/','https://[::1]/','https://project.local/','https://project.example.org:8443/','https://project.example.org/?key=SECRET','https://project.cn/','https://project.example.org/\nheader'])
def test_disallowed_url_never_reaches_dns(url):
    called=[]
    out=public_html.fetch_public_html(url,resolver=lambda *a,**k:called.append(a))
    assert out['status']=='UNAVAILABLE' and called==[]
    assert 'SECRET' not in str(out)


def addresses(*ips):return [(socket.AF_INET6 if ':' in ip else socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443)) for ip in ips]


@pytest.mark.parametrize('ips',[['127.0.0.1'],['10.0.0.1'],['169.254.169.254'],['224.0.0.1'],['1.1.1.1','127.0.0.1'],['::ffff:127.0.0.1']])
def test_private_mixed_or_multicast_dns_results_block_connection(ips):
    connects=[]
    out=public_html.fetch_public_html(URL,resolver=lambda *a,**k:addresses(*ips),connection_factory=lambda *a,**k:connects.append(a))
    assert out['status']=='UNAVAILABLE' and connects==[]


def test_dns_is_resolved_once_and_checked_ipv4_is_passed_to_connection():
    resolves=[];connections=[];requests=[]
    class Response:
        status=200
        def getheader(self,name,default=None):return 'text/html; charset=utf-8' if name=='Content-Type' else default
        def read(self,n):assert n==public_html.MAX_HTML_BYTES+1;return html()
    class Connection:
        def __init__(self,host,ip,timeout):connections.append((host,ip,timeout))
        def request(self,*args,**kwargs):requests.append((args,kwargs))
        def getresponse(self):return Response()
        def close(self):pass
    def resolve(*args,**kwargs):resolves.append(args);return addresses('1.1.1.1')
    out=public_html.fetch_public_html(URL,resolver=resolve,connection_factory=Connection)
    assert len(resolves)==1 and connections==[('project.example.org','1.1.1.1',5)]
    assert requests[0][0][:2]==('GET','/about')
    assert out['status']=='OK' and base64.b64decode(out['body_b64'])==html()


def test_parent_fetch_worker_has_timeout_minimal_environment_and_no_shell(monkeypatch):
    calls=[]
    def run(args,**kwargs):
        calls.append((args,kwargs))
        raise subprocess.TimeoutExpired(args,kwargs['timeout'])
    monkeypatch.setattr(public_html.subprocess,'run',run)
    out=public_html.read_public_html(URL)
    args,opts=calls[0]
    assert opts['timeout']==10 and opts['env']=={'LANG':'C'}
    assert '-I' in args and args[-1]==URL and opts.get('shell',False) is False
    assert out['reason']=='FETCH_TIMEOUT'


def test_collection_keeps_failure_and_alternative_claim_separate():
    calls=[]
    def fetch(url):
        calls.append(url)
        if 'pump.fun' in url:return {'status':'UNAVAILABLE','reason':'HTTP_403'}
        return {'status':'OK','body_b64':base64.b64encode(html()).decode()}
    out=PublicNarrativeClient(fetch=fetch,clock=lambda:100).collect(MINT,{'websites':[URL],'socials':[]})
    assert len(calls)==2 and len(out['evidence'])==1
    assert out['status']=='PARTIAL' and out['official_recognition']=='UNVERIFIED'
    assert out['attempts'][0]['reason']=='HTTP_403'
    assert out['search_coverage']=='BOUNDED_HINTS_ONLY'


def test_collection_caps_requests_and_never_recurses_through_page_links():
    calls=[]
    def fetch(url):calls.append(url);return {'status':'OK','body_b64':base64.b64encode(html(description='Source '+url+' describes a fictional cat exploring distant planets.',body='<a href="https://another.example.org/">More</a>')).decode()}
    out=PublicNarrativeClient(fetch=fetch,clock=lambda:100).collect(MINT,{'websites':[URL,'https://two.example.org/','https://three.example.org/'],'socials':[{'platform':'twitter','url':'https://x.com/fixture/status/123'}]})
    assert len(calls)==3 and len(out['evidence'])==3
    assert not any('another.example.org' in url for url in calls)
    assert out['exhaustive'] is False


def test_tls_connects_to_pinned_ip_but_verifies_original_hostname(monkeypatch):
    import ssl
    calls=[]
    class Sock:
        def close(self):pass
    class Context:
        check_hostname=True;verify_mode=ssl.CERT_REQUIRED
        def wrap_socket(self,sock,server_hostname):calls.append(('tls',server_hostname));return sock
    conn=public_html.PinnedHTTPSConnection('project.example.org','1.1.1.1')
    conn._context=Context()
    monkeypatch.setattr(public_html.socket,'create_connection',lambda address,timeout:(calls.append(('tcp',address)) or Sock()))
    conn.connect()
    assert calls==[('tcp',('1.1.1.1',443)),('tls','project.example.org')]
    conn._context.check_hostname=False
    with pytest.raises(ValueError):conn.connect()
    assert len(calls)==2


def test_provider_error_text_is_never_echoed():
    out=PublicNarrativeClient(fetch=lambda url:{'status':'UNAVAILABLE','reason':'SECRET_PROVIDER_TEXT'}).collect(MINT,{'websites':[]})
    assert 'SECRET_PROVIDER_TEXT' not in str(out)


def test_isolated_worker_script_rejects_local_url_without_package_imports():
    import sys
    result=subprocess.run([sys.executable,'-I',public_html.__file__,'--fetch','http://localhost/'],capture_output=True,timeout=3,env={'LANG':'C'})
    assert result.returncode==0
    assert json.loads(result.stdout)['reason']=='URL_NOT_ALLOWED'


def test_actual_analyzer_uses_public_claims_without_upgrading_official_ca_or_completeness(monkeypatch):
    from mission_agent.meme.cluster import WalletClusterAnalyzer,Holder,report_completeness,markdown
    a=WalletClusterAnalyzer(MINT,rpc=object(),narrative_client=PublicNarrativeClient(fetch=lambda url:{'status':'OK','body_b64':base64.b64encode(html(body=MINT)).decode()},clock=lambda:100))
    a.token_profile=lambda:{'status':'OK'}
    a.market_snapshot=lambda:{'status':'OK','source':'DEXSCREENER_API','mint':MINT,'websites':[URL]}
    a.holders=lambda:(1000,0,[Holder(key(1),key(301),100,0,'ORDINARY','fixture')])
    a._scan_holder=lambda *args:None;a._scan_funding=lambda *args:None
    report=a.analyze()
    assert report['narrative']['status']=='PARTIAL'
    assert report['narrative']['official_recognition']=='UNVERIFIED'
    assert report['assessment']['narrative_status']=='EXTERNAL_CLAIMS_PARTIAL'
    assert next(row for row in report['analysis_completeness']['requirements'] if row['id']=='narrative')['status']=='PARTIAL'
    assert report['analysis_completeness']['status']=='INCOMPLETE_EVIDENCE'
    assert 'External narrative source claims' in markdown(report)


def test_unverified_primary_identity_does_not_start_public_fetch():
    from mission_agent.meme.cluster import WalletClusterAnalyzer
    calls=[]
    a=WalletClusterAnalyzer(MINT,rpc=object(),narrative_client=PublicNarrativeClient(fetch=lambda url:calls.append(url)))
    assert a.narrative_snapshot({'status':'UNAVAILABLE'})['status']=='NOT_REQUESTED' and calls==[]


def test_standard_only_narrative_flag_keeps_legacy_paths_and_budgets():
    from mission_agent.mission_control.server import CLUSTER_PRESETS,CLUSTER_RPC_JOB_BUDGETS
    assert CLUSTER_PRESETS['standard']['collect_narrative'] is True
    assert not CLUSTER_PRESETS['quick'].get('collect_narrative')
    assert not CLUSTER_PRESETS['deep'].get('collect_narrative')
    assert CLUSTER_RPC_JOB_BUDGETS['standard']=={'max_wire_attempts':1200,'max_elapsed_seconds':1800}


def test_documented_platform_handle_maps_to_public_hint_not_verified_account():
    calls=[]
    out=PublicNarrativeClient(fetch=lambda url:(calls.append(url) or {'status':'UNAVAILABLE','reason':'HTTP_403'})).collect(MINT,{'websites':[],'socials':[{'platform':'twitter','handle':'@fixture'}]})
    assert calls==['https://pump.fun/coin/'+MINT,'https://x.com/fixture']
    assert out['official_recognition']=='UNVERIFIED'


def test_generic_platform_description_is_not_a_token_story():
    with pytest.raises(ValueError,match='NO_EXTRACTABLE_CLAIM'):
        extract_page_claim(html(description='Launch and trade memecoins on our platform.'),'https://pump.fun/coin/'+MINT,MINT,100)


def test_redirect_does_not_trigger_a_second_request_or_record_private_location():
    calls=[]
    class Response:
        status=302
        def getheader(self,*args):return 'https://127.0.0.1/SECRET'
    class Connection:
        def __init__(self,*args,**kwargs):pass
        def request(self,*args,**kwargs):calls.append(args)
        def getresponse(self):return Response()
        def close(self):pass
    result=public_html.fetch_public_html(URL,resolver=lambda *a,**k:addresses('1.1.1.1'),connection_factory=Connection)
    assert len(calls)==1 and result['reason']=='REDIRECT_NOT_FOLLOWED'
    assert 'SECRET' not in str(result)


def test_mirrored_page_claims_are_not_counted_as_independent_corroboration():
    out=PublicNarrativeClient(fetch=lambda url:{'status':'OK','body_b64':base64.b64encode(html()).decode()}).collect(MINT,{'websites':[URL]})
    assert len(out['evidence'])==1
    assert out['attempts'][1]['reason']=='DUPLICATE_CONTENT'
    assert out['official_recognition']=='UNVERIFIED'
