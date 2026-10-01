"""Read-only approved Solana RPC with <=2 requests/s and bounded retry."""
import json
import random
import time
import urllib.error
import urllib.request

RPC = 'https://api.mainnet.solana.com'
WALLET = '498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ'

class RPCFailure(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(str(code))

class SolanaRPC:
    def __init__(self, request=urllib.request.urlopen, sleep=time.sleep,
                 monotonic=time.monotonic, jitter=random.random, min_interval=.5):
        self.request, self.sleep, self.monotonic, self.jitter = request,sleep,monotonic,jitter
        self.last=None; self.calls=0; self.retries=0; self.rate_limits=0; self.min_interval=min_interval
    def call(self,method,params):
        if method not in ('getHealth','getSignaturesForAddress','getTransaction'):
            raise ValueError('READ_ONLY_METHOD_ALLOWLIST')
        body=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode()
        for attempt in range(3):
            if self.last is not None:self.sleep(max(0,self.min_interval-(self.monotonic()-self.last)))
            self.last=self.monotonic();self.calls+=1
            try:
                req=urllib.request.Request(RPC,data=body,headers={'Content-Type':'application/json'})
                with self.request(req,timeout=20) as response:value=json.loads(response.read())
                if value.get('error'):raise RPCFailure(value['error'].get('code','RPC_ERROR'))
                if 'result' not in value:raise RPCFailure('INCOMPLETE_RPC_ENVELOPE')
                return value['result']
            except urllib.error.HTTPError as exc:
                self.rate_limits+=exc.code==429
                if exc.code not in (429,500,502,503,504) or attempt==2:raise RPCFailure(exc.code) from None
                try:delay=float(exc.headers.get('Retry-After','0'))
                except ValueError:delay=0
                if delay>30:raise RPCFailure('RETRY_AFTER_EXCEEDS_BOUND') from None
            except (TimeoutError,urllib.error.URLError,OSError):
                if attempt==2:raise RPCFailure('TIMEOUT_OR_NETWORK') from None
                delay=0
            self.retries+=1;self.sleep(max(2**attempt,delay)+self.jitter()*.25)
    def signatures(self,before=None,until=None,limit=1000):
        options={'commitment':'finalized','limit':limit}
        if before:options['before']=before
        if until:options['until']=until
        value=self.call('getSignaturesForAddress',[WALLET,options])
        if not isinstance(value,list):raise RPCFailure('INVALID_SIGNATURE_LIST')
        return value
    def transaction(self,signature):
        return self.call('getTransaction',[signature,{'commitment':'finalized','encoding':'jsonParsed','maxSupportedTransactionVersion':1}])
