import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const script = fs.readFileSync(new URL('../mission_agent/mission_control/static/frank_research.js',import.meta.url),'utf8');
function browser(fetcher) {
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id,{value:'',textContent:'',innerHTML:'',disabled:false,events:{},
      addEventListener(name,fn){this.events[name]=fn;},click(){return this.events.click?.();}});
    return elements.get(id);
  };
  const calls=[];
  const context={document:{getElementById:get},fetch:async(path,opts)=>{
    calls.push({path,opts});
    return {ok:true,json:async()=>fetcher(path,opts)};
  },crypto:{randomUUID:()=> 'unique-key'},Date,Map,JSON,String,Number,Math,
  encodeURIComponent,setTimeout:fn=>{fn();}};
  vm.runInNewContext(script,context);
  return {get,calls};
}
const wait = async () => {for(let n=0;n<30;n++) await new Promise(resolve=>setImmediate(resolve));};
const positions = (mint='mint-A',next=null) => ({status:'OK',current_balance_verified:true,
  snapshot_id:'snapshot-A',observed_at:Date.now()/1000,age_seconds:'1',native_sol:{ui_amount:'0.5'},
  programs:[],account_count:75,mint_count:75,total_matching:75,returned:1,next_cursor:next,
  rows:[{mint,ui_amount:'18446744073709551615.123',account_count:2,model_state:'CLOSED',chain_state:'NONZERO'}]});

test('new source controls do not request source or local state on startup',()=>{
  const b=browser(()=>{throw Error('must not run');});
  assert.equal(b.calls.length,0);
});
test('explicit balance refresh posts once; subsequent status, market and positions are read-only',async()=>{
  const b=browser(path=>path.includes('balance-refresh')?{job_id:'jobA',state:'DONE',progress:{},errors:[]}:
    path.startsWith('/api/frank-positions')?positions():{rows:[],next_cursor:null});
  b.get('frank-source-balance').click(); await wait();
  assert.equal(b.calls.filter(c=>c.opts.method==='POST').length,1);
  assert.equal(b.calls[0].path,'/api/frank-balance-refresh');
  assert.ok(b.calls.slice(1).every(c=>c.opts.headers['X-Frank-Research-Read']==='1'));
  assert.match(b.get('frank-source-rows').innerHTML,/18446744073709551615\.123/);
  assert.match(b.get('frank-source-summary').textContent,/75/);
  assert.equal(b.calls.some(c=>/quote|cluster-analysis/.test(c.path)),false);
});
test('signals refresh explicitly selects signals; USD is never labelled USDC',async()=>{
  const b=browser(path=>path.includes('market-refresh')?{job_id:'market',state:'DONE',errors:[]}:
    path.startsWith('/api/frank-positions')?positions():{rows:[{mint:'mint-A',status:'OK',price_usd:'0.123',observed_at:Date.now()/1000}],next_cursor:null});
  b.get('frank-source-signals').click(); await wait();
  assert.equal(JSON.parse(b.calls[0].opts.body).scope,'signals');
  assert.match(b.get('frank-source-rows').innerHTML,/0\.123 USD\/token/);
  assert.doesNotMatch(b.get('frank-source-rows').innerHTML,/USDC/);
});
test('next page stays reachable and all market pages are consumed without total cap',async()=>{
  const b=browser(path=>path.startsWith('/api/frank-positions')?
    (path.includes('cursor=')?positions('mint-B'):positions('mint-A','p2')):
    path.includes('cursor=m2')?{rows:[{mint:'mint-A',status:'OK',price_usd:'9',observed_at:Date.now()/1000}],next_cursor:null}:
      {rows:[],next_cursor:'m2'});
  b.get('frank-source-read').click(); await wait();
  assert.match(b.get('frank-source-rows').innerHTML,/9 USD/);
  assert.equal(b.get('frank-source-next').disabled,false);
  b.get('frank-source-next').click(); await wait();
  assert.ok(b.calls.some(c=>c.path==='/api/frank-positions?limit=100&cursor=p2'));
  assert.match(b.get('frank-source-rows').innerHTML,/mint-B/);
});
test('late older query cannot replace a later Mint view; source content is escaped',async()=>{
  let resolveOld;
  const b=browser(path=>path.startsWith('/api/frank-positions')?
    (path.includes('mint=old')?new Promise(r=>{resolveOld=r;}):positions('<img src=x onerror=bad>')):
    {rows:[],next_cursor:null});
  b.get('frank-source-mint').value='old';b.get('frank-source-find').click();
  await new Promise(r=>setImmediate(r));
  b.get('frank-source-mint').value='new';b.get('frank-source-find').click();await wait();
  resolveOld(positions('old')); await wait();
  assert.match(b.get('frank-source-rows').innerHTML,/&lt;img/);
  assert.doesNotMatch(b.get('frank-source-rows').innerHTML,/<img|<code>old/);
});
