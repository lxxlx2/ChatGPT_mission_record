"""Lossless finalized RPC export. Page cursor advances only after durable transaction writes."""
import json, os, sqlite3, time, urllib.request, urllib.error
class DataSourceUnavailable(Exception): pass
class RawSolanaProvider:
    def __init__(self,url,page_size=100): self.url=url;self.page_size=page_size
    def rpc(self,method,params):
        for attempt in range(4):
            try:
                request=urllib.request.Request(self.url,json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),{'Content-Type':'application/json'})
                with urllib.request.urlopen(request,timeout=12) as response: data=json.load(response)
                if 'error' in data: raise DataSourceUnavailable('RPC_ERROR_'+str(data['error'].get('code','UNKNOWN')))
                return data['result']
            except (urllib.error.URLError,TimeoutError,DataSourceUnavailable) as error:
                if attempt==3:
                    reason=str(error) if isinstance(error,DataSourceUnavailable) else 'HTTP_'+str(error.code) if isinstance(error,urllib.error.HTTPError) else type(error).__name__.upper()
                    raise DataSourceUnavailable(reason) from None
                time.sleep(min(2**attempt,4))
    def signatures(self,address,before=None):
        config={'limit':self.page_size,'commitment':'finalized'}
        if before: config['before']=before
        return self.rpc('getSignaturesForAddress',[address,config])
    def transaction(self,signature):
        return self.rpc('getTransaction',[signature,{'encoding':'jsonParsed','commitment':'finalized','maxSupportedTransactionVersion':0}])
class AlchemyProvider(RawSolanaProvider): pass
class HeliusProvider(RawSolanaProvider): pass
class IndexerProvider:
    """Adapter contract: finalized signatures(address,before), transaction(signature)."""
    def signatures(self,address,before=None): raise DataSourceUnavailable('INDEXER_ADAPTER_UNCONFIGURED')
    def transaction(self,signature): raise DataSourceUnavailable('INDEXER_ADAPTER_UNCONFIGURED')
class CachedFixtureProvider:
    def __init__(self,pages,transactions): self.pages=pages; self.transactions=transactions
    def signatures(self,address,before=None): return self.pages.get((address,before),[])
    def transaction(self,signature): return self.transactions.get(signature)
def configured_provider():
    if os.environ.get('SOLANA_RPC_URL'): return RawSolanaProvider(os.environ['SOLANA_RPC_URL']),'SOLANA_RPC_URL'
    if os.environ.get('ALCHEMY_API_KEY'): return AlchemyProvider('https://solana-mainnet.g.alchemy.com/v2/'+os.environ['ALCHEMY_API_KEY']),'ALCHEMY_API_KEY'
    if os.environ.get('HELIUS_API_KEY'): return HeliusProvider('https://mainnet.helius-rpc.com/?api-key='+os.environ['HELIUS_API_KEY']),'HELIUS_API_KEY'
    return RawSolanaProvider('https://api.mainnet-beta.solana.com'),'PUBLIC_SOLANA_RPC'
class Exporter:
    def __init__(self,path,provider):
        self.db=sqlite3.connect(path); self.provider=provider
        self.db.executescript('CREATE TABLE IF NOT EXISTS transactions(signature TEXT PRIMARY KEY, payload TEXT NOT NULL); CREATE TABLE IF NOT EXISTS checkpoints(wallet TEXT PRIMARY KEY, cursor TEXT, last_slot INTEGER, complete INTEGER NOT NULL DEFAULT 0); CREATE TABLE IF NOT EXISTS wallet_signatures(wallet TEXT,signature TEXT,PRIMARY KEY(wallet,signature));')
    def export(self,wallet,max_pages=1):
        row=self.db.execute('SELECT cursor,last_slot,complete FROM checkpoints WHERE wallet=?',(wallet,)).fetchone()
        cursor=row[0] if row else None
        last_slot=row[1] if row else None
        if row and row[2]: return
        for _ in range(max_pages):
            page=self.provider.signatures(wallet,cursor)
            if not page:
                with self.db: self.db.execute('INSERT OR REPLACE INTO checkpoints VALUES(?,?,?,1)',(wallet,cursor,last_slot))
                return
            # Fetches may fail midway; individual payloads remain reusable, cursor does not skip missing rows.
            for item in page:
                sig=item['signature']
                if not self.db.execute('SELECT 1 FROM transactions WHERE signature=?',(sig,)).fetchone():
                    tx=self.provider.transaction(sig)
                    if tx is None: raise DataSourceUnavailable('TRANSACTION_UNAVAILABLE')
                    with self.db: self.db.execute('INSERT INTO transactions VALUES(?,?)',(sig,json.dumps(tx)))
                with self.db: self.db.execute('INSERT OR IGNORE INTO wallet_signatures VALUES(?,?)',(wallet,sig))
            if page[-1]['signature']==cursor: raise DataSourceUnavailable('PAGINATION_CURSOR_STALLED')
            cursor=page[-1]['signature'];last_slot=page[-1]['slot']
            with self.db: self.db.execute('INSERT OR REPLACE INTO checkpoints VALUES(?,?,?,0)',(wallet,cursor,page[-1]['slot']))
    def checkpoint(self):
        return [dict(zip(['wallet','last_signature','last_slot','complete'],r)) for r in self.db.execute('SELECT * FROM checkpoints ORDER BY wallet')]
    def transactions(self): return [(s,json.loads(p)) for s,p in self.db.execute('SELECT * FROM transactions')]
