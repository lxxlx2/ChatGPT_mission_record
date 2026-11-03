"""Temporary CA browser fixture: real Handler/manager, synthetic analyzer, no network.

Invoked only by test_frank_ca_browser.mjs. No DashboardState/production root,
provider clients, keys or production files. The fixture exits when stdin closes.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from urllib.parse import urlparse
import json
import base64
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mission_agent.mission_control import server  # noqa: E402


def offline_audit(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'}:
        raise RuntimeError('OFFLINE_FIXTURE_NETWORK_OR_PROCESS_DENIED')
    if event == 'socket.bind' and args[1] != ('127.0.0.1', 0):
        raise RuntimeError('ONLY_RANDOM_LOOPBACK_FIXTURE_BIND_ALLOWED')


sys.addaudithook(offline_audit)


class FixtureRPC:
    def __init__(self, *args, **kwargs):
        self.calls = 0

    def assert_can_publish(self):
        pass


def fixture_holder_binary(mint):
    from mission_agent.meme.pool_vaults import _key
    from mission_agent.meme.holder_binary import collect_holder_binary_check
    program='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
    owner=lambda i:_key((6000+i).to_bytes(32,'big'))
    addresses=[_key((5000+i).to_bytes(32,'big')) for i in range(30)]
    amounts=[100,700]+[20]*10+[0]*18
    accounts=[{'token_account':a,'owner':owner(0 if i<2 else i-1),'raw':str(amounts[i]),'decimals':6} for i,a in enumerate(addresses)]
    source={'requested':True,'status':'COMPLETE_SNAPSHOT','mint':mint,'program_id':program,'snapshot_slot':100,'supply_slot':100,
        'response_sha256':'a'*64,'account_count':30,'nonzero_owner_count':11,'normalization_complete':True,'decimals':6,'supply_raw':'1000','total_raw':'1000',
        'metrics':{'GLOBAL_OWNER_TOP10_PCT':'98.0000','GLOBAL_EX_LP_OWNER_TOP10_PCT':'20.0000'},'accounts':accounts,
        'owners':[{'owner':owner(i),'raw':'800' if i==0 else '20','account_count':2 if i==0 else 1,'role':'LP' if i==0 else 'ORDINARY','supply_pct':'80.0000' if i==0 else '2.0000','history_scanned':False} for i in range(11)]}
    def encoded(data):return {'owner':program,'executable':False,'data':[base64.b64encode(data).decode(),'base64']}
    m=bytearray(82);m[36:44]=(1000).to_bytes(8,'little');m[44]=6;m[45]=1
    # Decode the syntactically supplied Mint for actual binary fixture fields.
    from mission_agent.meme.holder_ranks import ALPHABET
    value=0
    for c in mint:value=value*58+ALPHABET.index(c)
    if value.bit_length()>256:return source
    mint_key=value.to_bytes(32,'big')
    values={}
    for i,a in enumerate(addresses):
        b=bytearray(165);b[:32]=mint_key;b[32:64]=(6000+(0 if i<2 else i-1)).to_bytes(32,'big')
        b[64:72]=amounts[i].to_bytes(8,'little');b[108]=1
        values[a]=encoded(b)
    class BinaryRPC:
        def call(self,method,params,ttl=0):
            assert method=='getMultipleAccounts' and params[0][0]==mint
            return {'context':{'slot':101},'value':[encoded(m)]+[values[a] for a in params[0][1:]]}
    source['raw_balance_check']=collect_holder_binary_check(mint,source,BinaryRPC())
    return source


def fixture_special_roles(mint,source,market):
    from mission_agent.meme.pool_vaults import _key,PROGRAM,POOL_DISCRIMINATOR
    from mission_agent.meme.pool_programs import pubkey_bytes,WHIRLPOOL
    from mission_agent.meme.special_roles import collect_special_roles
    from mission_agent.meme.holder_ranks import valid_pubkey
    if not valid_pubkey(mint):return {"status":"NOT_REQUESTED"}
    pool1=_key((6000).to_bytes(32,'big'));pool2=_key((6001).to_bytes(32,'big'))
    quote=_key((5).to_bytes(32,'big'));vquote=_key((7).to_bytes(32,'big'))
    def enc(owner,b):return {'owner':owner,'executable':False,'data':[base64.b64encode(b).decode(),'base64']}
    b=bytearray(287);b[:8]=POOL_DISCRIMINATOR
    for offset,value in [(43,mint),(75,quote),(139,_key((5000).to_bytes(32,'big'))),(171,vquote)]:b[offset:offset+32]=pubkey_bytes(value)
    pump=enc(PROGRAM,b)
    import hashlib
    b=bytearray(653);b[:8]=hashlib.sha256(b'account:Whirlpool').digest()[:8]
    for offset,value in [(101,mint),(181,quote),(133,_key((5002).to_bytes(32,'big'))),(213,vquote)]:b[offset:offset+32]=pubkey_bytes(value)
    orca=enc(WHIRLPOOL,b)
    program='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
    m=bytearray(82);m[36:44]=(1000).to_bytes(8,'little');m[44]=6;m[45]=1
    values={mint:enc(program,m),pool1:pump,pool2:orca}
    for row in source['accounts']:
        b=bytearray(165);b[:32]=pubkey_bytes(mint);b[32:64]=pubkey_bytes(row['owner']);b[64:72]=int(row['raw']).to_bytes(8,'little');b[108]=1
        values[row['token_account']]=enc(program,b)
    class RPC:
        def call(self,method,params,ttl=0):
            assert method=='getMultipleAccounts' and len(params[0])<=100
            return {'context':{'slot':101},'value':[values[a] for a in params[0]]}
    from mission_agent.meme.holder_ranks import discover_owner_pool_hint
    from mission_agent.meme.special_roles import digest
    owner_response={'context':{'slot':101},'value':[orca]}
    hint=discover_owner_pool_hint(mint,pool2,orca,101,source['snapshot_slot'],source['response_sha256'],digest(owner_response),{r['token_account']:r['owner'] for r in source['accounts']})
    assert hint is not None
    source['owner_pool_hints']=[hint]
    source['owner_pool_discovery']={'hints_not_selected':0,'additional_rpc_calls':0}
    return collect_special_roles(mint,source,market,RPC())


class FixtureAnalyzer:
    count = 0

    def __init__(self, mint, **kwargs):
        self.mint = mint
        self.progress = kwargs['progress_callback']

    def analyze(self):
        type(self).count += 1
        name = f'SYNTHETIC_REPORT_{type(self).count}'
        self.progress('TOKEN_PROFILE', {'fixture': True})
        time.sleep(0.15)
        if self.mint == '4' * 32:
            raise ValueError('FIXTURE_ANALYZER_ERROR')
        from mission_agent.meme.pool_vaults import _key
        pool_addr=_key((6000).to_bytes(32,'big'));pool_vault=_key((5000).to_bytes(32,'big'))
        report={
            'schema_version': 2, 'source': 'SOLANA_FINALIZED_JSON_RPC',
            'mint': self.mint, 'observed_at': time.time(),
            'coverage': {'special_normalization_complete': False,
                         'deep_holders_scanned': 1, 'top_accounts_resolved': 1,
                         'historical_account_history':[{'owner':self.mint,'account':'1'*31+'4','selected':False,'stop_reason':'FRONTIER_LIMIT','history_complete':False}],
                         'owner_account_history': [{'owner':self.mint,'account_source_status':'VERIFIED_CURRENT_MINT_ACCOUNTS',
                             'current_accounts_observed':3,'accounts_selected':['1'*31+'2','1'*31+'3'],
                             'accounts_with_windows':['1'*31+'2','1'*31+'3'],'accounts_not_selected':1,
                             'account_selection_complete':False,'selection_stop_reason':'REPORT_EXTRA_ACCOUNT_LIMIT',
                             'closed_account_history':'NOT_ENUMERATED','history_complete':False}],
                         'history_windows': [{'owner': self.mint, 'address':'1'*31+'3', 'phase': 'holder', 'pages': 4,
                             'signature_count': 120, 'page_size': 30, 'stop_reason': 'PAGE_LIMIT',
                             'next_before': 'FIXTURE_PUBLIC_CURSOR', 'history_complete': False}],
                         'gaps': ['HISTORY_PAGINATION_INCOMPLETE']},
            'holder_rankings':fixture_holder_binary(self.mint),
            'historical_account_evidence':[{'owner':self.mint,'account':'1'*31+'4',
                'signature':'FIXTURE_HISTORICAL_PROOF','slot':90,'block_time':90,
                'balance_phase':'pre','raw':'10','decimals':0,
                'closure_at_transaction_end':'CONFIRMED_CLOSED_AT_TRANSACTION_END','response_sha256':'a'*64}],
            'pool_vaults':{'version':1,'source':'SOLANA_FINALIZED_RAW_ACCOUNTS','pool_program':'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA','status':'VAULT_BALANCE_SNAPSHOT','mint':self.mint,'pool_address':pool_addr,
                'discovery_slot':100,'snapshot_slot':101,'observed_at':103,'response_sha256':'a'*64,'raw_vault_quote_per_target':'2','price_usd':'UNVERIFIED',
                'liquidity_usd':'UNVERIFIED','executable_quote':'NOT_COMPUTED','flags':['VIRTUAL_QUOTE_RESERVES_PRESENT'],
                'target':{'mint':self.mint,'vault':pool_vault,'authority':pool_addr,'raw':'100','decimals':6,'quantity':'0.000100','token_program':'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','mint_supply_raw':'1000'},
                'quote':{'mint':'1'*31+'6','vault':'1'*31+'8','authority':pool_addr,'raw':'200','decimals':6,'quantity':'0.000200'},
                'market_comparison':{'version':1,'status':'UNALIGNED_RATIO_COMPARISON','mint':self.mint,'quote_address':'1'*31+'6','pool_address':pool_addr,
                    'model_quote_per_target':'1.85','indexer_quote_per_target':'1.9','indexer_field':'base_token_price_quote_token',
                    'snapshot_slot':101,'same_chain_snapshot':False,'provider_asof':'UNVERIFIED','price_basis_alignment':'UNVERIFIED',
                    'chain_response_sha256':'a'*64,'indexer_response_sha256':'b'*64,
                    'chain_result_received_at':103,'indexer_result_received_at':102,'retrieval_gap_seconds':1,
                    'difference_indexer_minus_model':'0.05','difference_pct_of_model':'2.7027'},
                'effective_reserves':{'version':1,'status':'DERIVED_PROTOCOL_RESERVES','formula':'PUMPSWAP_SIGNED_VQR_V1',
                    'protocol_base_mint':self.mint,'protocol_quote_mint':'1'*31+'6','target_mint':self.mint,'quote_mint':'1'*31+'6',
                    'base_raw':'100','base_decimals':6,'quote_decimals':6,'quote_vault_raw':'200','waiting_fees_raw':'15',
                    'virtual_quote_raw':'-15','real_quote_raw':'185','boost_component_raw':'0','effective_quote_raw':'185',
                    'quote_vault_quantity':'0.000200','waiting_fees_quantity':'0.000015','real_quote_quantity':'0.000185',
                    'boost_component_quantity':'0.000000','effective_quote_quantity':'0.000185','effective_quote_per_target':'1.85',
                    'documented_zero_defaults':[],'deployed_binary_semantics':'UNVERIFIED'}},
            'narrative':{'version':1,'status':'PARTIAL','official_recognition':'UNVERIFIED','exhaustive':False,'search_coverage':'BOUNDED_HINTS_ONLY',
                'evidence':[{'classification':'THIRD_PARTY_CLAIM','source_url':'https://project.example.org/',
                    'publisher_host':'project.example.org','title':'Fixture project story','excerpt':'A fictional cat explores distant planets.',
                    'exact_ca_mentioned':False,'published_at_claim':None,'first_seen_at':100,'response_sha256':'a'*64}],
                'attempts':[{'kind':'LAUNCHPAD_PAGE','status':'UNAVAILABLE','reason':'HTTP_403','requested':True}]},
            'holders': [], 'metrics': {}, 'assessment': {}, 'token_profile': {},
            'market': {'status':'OK','source':'DEXSCREENER_API','name':name,'symbol':'FIXTURE','mint':self.mint,'observed_at':100,
                'price_usd':'2','main_pair':{'pair_address':pool_addr,'base_address':self.mint,'quote_address':'1'*31+'6','liquidity_usd':'1000'},
                'independent_market':{'status':'OK','source':'GECKOTERMINAL_PUBLIC_API','attempted':True,'mint':self.mint,'pool_address':pool_addr,'quote_address':'1'*31+'6','observed_at':102,'target_orientation':'BASE','price_quote_units':'1.9','price_quote_units_field':'base_token_price_quote_token','response_sha256':'b'*64},
                'comparison':{'status':'INDEXER_SNAPSHOTS_COMPARED','mint':self.mint,'pool_address':pool_addr,'quote_address':'1'*31+'6','same_chain_snapshot':False,'provider_asof':'UNVERIFIED','retrieval_gap_seconds':2,
                    'metrics':{'price_usd':{'status':'COMPARED','primary':'2','independent':'2.5','difference':'0.5','difference_pct_of_primary':'25.0000'},
                              'pool_liquidity_usd':{'status':'COMPARED','primary':'1000','independent':'900','difference':'-100','difference_pct_of_primary':'-10.0000'}}}},
            'limitations': ['SYNTHETIC_ONLY_NO_CHAIN_REQUEST'],
        }
        from mission_agent.meme.pool_holder_roles import attach_pool_holder_roles
        report['pool_holder_roles']=attach_pool_holder_roles(self.mint,report['holder_rankings'],report['pool_vaults'])
        report['special_address_roles']=fixture_special_roles(self.mint,report['holder_rankings'],report['market'])
        from mission_agent.meme.special_roles import withhold_legacy_normalization
        withhold_legacy_normalization(report['holder_rankings'],report['special_address_roles'])
        return report


server.SolanaReadOnlyRPC = FixtureRPC
server.WalletClusterAnalyzer = FixtureAnalyzer
server.load_registry = lambda _: {}

with TemporaryDirectory(prefix='frank-ca-browser-') as scratch:
    # Deliberately do not call DashboardState or manager __init__ (providers).
    manager = object.__new__(server.ClusterJobManager)
    manager.lock = threading.Lock()
    manager.jobs = {}
    manager.max_retained_jobs = 64
    manager.report_root = Path(scratch) / 'reports'
    manager.report_root.mkdir()
    manager.cache_path = Path(scratch) / 'cache.sqlite'
    manager.rpc_endpoints = ['https://disabled.invalid']
    manager.rpc_endpoint = manager.rpc_endpoints[0]
    manager.registry_path = Path(scratch) / 'registry.json'
    manager.market_client = None
    manager.evidence_enabled = False
    manager.executor = ThreadPoolExecutor(max_workers=1)

    # Explicit synthetic D2 data only, served through the product's real
    # same-origin GET handler. No private source import or RPC is involved.
    observed = datetime.fromtimestamp(time.time() - 3600, timezone.utc).isoformat()
    d2_fixture = {
        'status': 'BALANCE_AT_OBSERVED_FINALIZED_SLOTS_NOT_LIVE',
        'observed_at_utc': observed, 'observed_at_bangkok': observed,
        'age_seconds_at_response': 3600,
        'account_count': 2, 'mint_count': 1,
        'program_coverage': [
            {'program_id': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA', 'slot': 100},
            {'program_id': 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb', 'slot': 101},
        ],
        'page': 0, 'total_pages': 1, 'result_count': 1,
        'rows': [{'mint': '2' * 32, 'raw_amount': '12000000', 'decimals': 6,
                  'account_count': 2, 'slot_min': 100, 'slot_max': 101}],
    }

    class FixtureHandler(server.Handler):
        state = SimpleNamespace(
            cluster_jobs=manager,
            follow_opportunities=lambda: server.partition_source_only(
                [], now=time.time(), runtime_status='LIVE'),
            frank_d2_at_slot=lambda **_: d2_fixture,
        )
        static_root = Path(server.__file__).parent / 'static'

        def log_message(self, *args):
            pass

        def do_GET(self):
            path = urlparse(self.path).path
            if path == '/__fixture/reset-memory':
                # Test-only equivalent of a new manager reading disk, no lifecycle action.
                with manager.lock:
                    manager.jobs.clear()
                return self._json({'cleared': True})
            if path.startswith('/api/') and path not in {
                '/api/cluster-analysis', '/api/cluster-latest',
                '/api/follow-opportunities', '/api/frank-d2-at-slot',
            }:
                lists = {'/api/candidates', '/api/trades', '/api/decisions', '/api/review-activity'}
                return self._json([] if path in lists else {'status': 'TEST_FIXTURE', 'rows': [], 'summary': {}})
            return super().do_GET()

        def do_POST(self):
            # The only POST exercises the real submit/worker with the analyzer replaced above.
            return super().do_POST()

    httpd = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(json.dumps({'port': httpd.server_port, 'pid': __import__('os').getpid()}), flush=True)
    try:
        sys.stdin.read()
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=3)
        manager.executor.shutdown(wait=True)
