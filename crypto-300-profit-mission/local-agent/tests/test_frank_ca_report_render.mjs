import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

// Runs the COMPLETE shipped browser app.js instead of extracting or mocking
// renderClusterReport. The DOM is deliberately small: actual Chrome behavior
// remains gated by the separate Mac fixture-browser acceptance.
const source=readFileSync(new URL('../mission_agent/mission_control/static/app.js',import.meta.url),'utf8');
const mint='22222222222222222222222222222222';
const jobId='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
const fixture={
  mint,observed_at:1792683606,
  coverage:{special_normalization_complete:false,top_accounts_resolved:1,deep_holders_scanned:1,rpc_endpoint_failures:{}},
  market:{status:'UNAVAILABLE',name:'FIXTURE_REPORT',symbol:'QA',main_pair:{}},
  metrics:{},assessment:{chain_permission_status:'UNRESOLVED',cluster_status:'WALLET_CLUSTER_UNRESOLVED'},
  token_profile:{status:'UNAVAILABLE'},holders:[],limitations:['FIXTURE_ONLY_NOT_CHAIN_DATA'],
  transaction_errors:[],
};

function harness(options = {}) {
  const elements=new Map();
  const classes={add(){},remove(){},toggle(){}};
  const element=(id)=>{
    if (!elements.has(id)) elements.set(id,{
      id,hidden:true,disabled:false,value:'',textContent:'',innerHTML:'',className:'',classList:classes,
      style:{},dataset:{},listeners:new Map(),
      addEventListener(name,callback){this.listeners.set(name,callback)},
      querySelectorAll:()=>[],appendChild(){},remove(){},focus(){},select(){},
    });
    return elements.get(id);
  };
  const store=options.store || new Map(),requests=[];
  let responseFor=options.responseFor || null;
  const context={
    document:{
      getElementById:element,querySelectorAll:()=>[],
      addEventListener(){},body:{appendChild(){}},createElement:()=>element('__created'),
    },
    window:{location:{hash:'#cluster'},addEventListener(){}},
    history:{replaceState(){}},
    navigator:{clipboard:{writeText:async()=>{}}},
    localStorage:{
      getItem:k=>{if(options.storageReadError) throw new Error('SecurityError');return store.get('local:'+k)||null;},
      setItem:(k,v)=>{if(options.storageWriteError) throw new Error('QuotaExceededError');store.set('local:'+k,v);},
      removeItem:k=>store.delete('local:'+k),
    },
    sessionStorage:{getItem:k=>store.get('session:'+k)||null,setItem:(k,v)=>store.set('session:'+k,v),removeItem:k=>store.delete('session:'+k)},
    fetch:async(url,options={})=>{
      requests.push({url,method:options.method||'GET'});
      if (responseFor) return responseFor(url,options);
      if (options.method==='POST') throw new TypeError('fixture submission failed');
      if(url==='/api/cluster-latest?mint='+encodeURIComponent(mint)+'&job_id='+jobId)
        return {ok:true,status:200,json:async()=>fixture};
      if(url==='/api/cluster-analysis?job_id='+jobId)
        return {ok:true,status:200,json:async()=>({job_id:jobId,mint,status:'DONE'})};
      // Other startup polling must not hit any real external service
      return await new Promise(()=>{});
    },
    setInterval:()=>0,setTimeout:()=>0,clearTimeout(){},
    console:{warn(){},error(){}},
    Date,Math,Number,String,JSON,URL,URLSearchParams,Intl,
  };
  vm.createContext(context);
  if (options.initialMint) element('cluster-mint').value=options.initialMint;
  vm.runInContext(source,context,{timeout:2500,filename:'app.js'});
  return {context,element,requests,store,setResponse(fn){responseFor=fn;}};
}

test('startup historical load labels the remembered CA as unverified and uses GET only',async()=>{
  const store=new Map([['local:mission-meme-last-cluster-ca',mint]]);
  const h=harness({store,responseFor:async url=>url.startsWith('/api/cluster-latest?')
    ? {ok:true,status:200,json:async()=>fixture} : new Promise(()=>{})});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.element('cluster-mint').value,mint);
  assert.equal(h.element('cluster-result').hidden,false);
  assert.match(h.element('cluster-status').innerHTML,/已有历史报告/);
  assert.match(h.element('cluster-status').innerHTML,/与当前任务的关联未经核实/);
  assert.deepEqual(h.requests.filter(x=>x.url.startsWith('/api/cluster-latest?')),
    [{url:'/api/cluster-latest?mint='+mint,method:'GET'}]);
  assert.equal(h.requests.filter(x=>x.method==='POST').length,0);
});

test('startup prefilled CA takes precedence over the previous CA cache',async()=>{
  const selected='33333333333333333333333333333333';
  const store=new Map([['local:mission-meme-last-cluster-ca',mint]]);
  const h=harness({store,initialMint:selected,responseFor:async url=>url.startsWith('/api/cluster-latest?')
    ? {ok:true,status:200,json:async()=>({...fixture,mint:selected})} : new Promise(()=>{})});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.element('cluster-mint').value,selected);
  assert.deepEqual(h.requests.filter(x=>x.url.startsWith('/api/cluster-latest?')),
    [{url:'/api/cluster-latest?mint='+selected,method:'GET'}]);
  assert.match(h.element('cluster-status').innerHTML,/与当前任务的关联未经核实/);
  assert.equal(h.requests.filter(x=>x.method==='POST').length,0);
});

test('startup historical cache cannot preempt a pending task',async()=>{
  const store=new Map([
    ['local:mission-meme-last-cluster-ca',mint],
    ['session:mission-meme-cluster-pending-v1',JSON.stringify({id:jobId,mint})],
  ]);
  const h=harness({store});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.requests.filter(x=>x.url.startsWith('/api/cluster-latest?')).length,0);
  assert.equal(JSON.parse(h.store.get('session:mission-meme-cluster-pending-v1')).id,jobId);
});

test('failed history lookup for another CA hides the previously rendered report',async()=>{
  const h=harness();
  await finish(h,jobId,'OLD_CA_REPORT');
  assert.equal(h.element('cluster-result').hidden,false);
  h.element('cluster-preview').hidden=false;
  h.element('cluster-mint').value='33333333333333333333333333333333';
  const response=deferred();
  h.setResponse(async()=>response.promise);
  const reading=h.element('cluster-read-cached').listeners.get('click')();
  assert.equal(h.element('cluster-result').hidden,true);
  assert.equal(h.element('cluster-preview').hidden,true);
  response.resolve({ok:false,status:404,json:async()=>({})});
  await reading;
  assert.equal(h.element('cluster-result').hidden,true);
  assert.match(h.element('cluster-status').innerHTML,/历史缓存读取失败/);
  assert.equal(h.requests.filter(x=>x.method==='POST').length,0);
});

test('full shipped app.js directly renders a verified-shape incomplete CA report',()=>{
  const h=harness();
  // Calls the real report renderer, not a test substitute.
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:fixture}),{timeout:2500});
  assert.equal(h.element('cluster-result').hidden,false);
  assert.match(h.element('cluster-summary').innerHTML,/FIXTURE_REPORT/);
  assert.match(h.element('cluster-metrics').innerHTML,/cluster-metric/);
  assert.match(h.element('cluster-coverage').innerHTML,/覆盖|RPC/);
  assert.match(h.element('cluster-status').innerHTML,/归一化尚未完成/);
  assert.doesNotMatch(h.element('cluster-status').className,/done/);
  assert.equal(h.requests.filter(x=>x.method==='POST').length,0);
});

test('full script DONE -> existing report GET -> pending cleared without phantom render failure',async()=>{
  const h=harness();
  h.element('cluster-mint').value=mint;
  vm.runInContext('clusterSetJob(__id,__mint)',Object.assign(h.context,{__id:jobId,__mint:mint}),{timeout:2500});
  await vm.runInContext('pollClusterJob(__id)',h.context,{timeout:2500});
  assert.match(h.element('cluster-summary').innerHTML,/FIXTURE_REPORT/);
  assert.equal(h.requests.filter(x=>x.url.startsWith('/api/cluster-analysis?job_id=')).length,1);
  assert.equal(h.requests.filter(x=>x.url.startsWith('/api/cluster-latest')).length,1);
  assert.equal(h.requests.filter(x=>x.method==='POST').length,0);
  assert.equal(h.store.has('session:mission-meme-cluster-pending-v1'),false);
  assert.equal(h.element('cluster-submit').disabled,false);
  assert.equal(h.element('cluster-recovery').hidden,true);
  assert.match(h.element('cluster-status').innerHTML,/无法独立证明与本次分析一一对应/);
});

const secondJob='bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';
const historyKey='mission-meme-cluster-reports-v1';
async function finish(h,id,name='REPORT') {
  h.element('cluster-mint').value=mint;
  h.setResponse(async url=>({ok:true,status:200,json:async()=>
    url.startsWith('/api/cluster-analysis?') ? {job_id:id,mint,status:'DONE'} :
      {...fixture,ca_job_id:id,market:{...fixture.market,name}}}));
  h.context.__id=id;h.context.__mint=mint;
  vm.runInContext('clusterSetJob(__id,__mint)',h.context);
  await vm.runInContext('pollClusterJob(__id)',h.context);
}

test('history read is visible outside transient task recovery controls',()=>{
  const html=readFileSync(new URL('../mission_agent/mission_control/static/index.html',import.meta.url),'utf8');
  const recovery=html.match(/<div id="cluster-recovery"[\s\S]*?<\/div>/)[0];
  assert.doesNotMatch(recovery,/id="cluster-read-cached"/);
  assert.match(html,/id="cluster-reports"/);
});

test('completed A and B survive a new page; selecting A reads exact ID without POST',async()=>{
  const h=harness();
  await finish(h,jobId,'REPORT_A');await finish(h,secondJob,'REPORT_B');
  const saved=JSON.parse(h.store.get('local:'+historyKey));
  assert.equal(saved.length,2);assert.equal(saved[0].id,secondJob);
  assert.equal(h.store.has('session:mission-meme-cluster-pending-v1'),false);
  const restored=harness({store:h.store});
  assert.match(restored.element('cluster-reports').innerHTML,new RegExp(jobId));
  restored.element('cluster-reports').value=jobId;
  restored.setResponse(async url=>({ok:true,status:200,json:async()=>
    url.startsWith('/api/cluster-analysis?') ? {job_id:jobId,mint,status:'DONE'} :
      {...fixture,ca_job_id:jobId,market:{...fixture.market,name:'REPORT_A'}}}));
  await restored.element('cluster-read-report').listeners.get('click')();
  await new Promise(resolve=>setImmediate(resolve));
  assert.match(restored.element('cluster-summary').innerHTML,/REPORT_A/);
  assert.ok(restored.requests.some(x=>x.url.includes('&job_id='+jobId)));
  assert.equal(restored.requests.filter(x=>x.method==='POST').length,0);
});

test('invalid CA preserves pending identity and does not attempt submission',async()=>{
  const h=harness();
  h.context.__id=jobId;h.context.__mint=mint;
  vm.runInContext('clusterSetJob(__id,__mint)',h.context);
  h.element('cluster-mint').value='bad CA';h.element('cluster-preset').value='quick';
  await h.element('cluster-form').listeners.get('submit')({preventDefault(){}});
  assert.equal(h.requests.filter(x=>x.method==='POST').length,0);
  assert.equal(JSON.parse(h.store.get('session:mission-meme-cluster-pending-v1')).id,jobId);
  assert.match(h.element('cluster-status').innerHTML,/完整.*Solana CA/);
});

test('explicit historical lookup uses entered Mint and keeps the other pending task',async()=>{
  const h=harness(), otherMint='33333333333333333333333333333333';
  h.context.__id=jobId;h.context.__mint=mint;
  vm.runInContext('clusterSetJob(__id,__mint)',h.context);
  h.element('cluster-mint').value=otherMint;
  h.setResponse(async url=>({ok:true,status:200,json:async()=>({...fixture,mint:otherMint})}));
  await h.element('cluster-read-cached').listeners.get('click')();
  assert.equal(h.requests.at(-1).url,'/api/cluster-latest?mint='+otherMint);
  assert.equal(JSON.parse(h.store.get('session:mission-meme-cluster-pending-v1')).id,jobId);
  assert.match(h.element('cluster-status').innerHTML,/覆盖仍不完整.*关联未经核实/);
  h.setResponse(async url=>({ok:true,status:200,json:async()=>({job_id:jobId,mint,status:'RUNNING'})}));
  h.element('cluster-resume-get').listeners.get('click')();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.element('cluster-mint').value,mint);
});

test('report shortcuts are bounded, validated and contain no report payload',async()=>{
  const h=harness();
  for(let i=1;i<=12;i++) await finish(h,i.toString(16).padStart(32,'0'));
  const saved=JSON.parse(h.store.get('local:'+historyKey));
  assert.equal(saved.length,10);
  assert.deepEqual(Object.keys(saved[0]).sort(),['id','mint','observed_at']);
  const bad=harness({store:new Map([['local:'+historyKey,JSON.stringify([{id:'<script>',mint,observed_at:1}])]])});
  assert.equal(bad.element('cluster-read-report').disabled,true);
  assert.doesNotMatch(bad.element('cluster-reports').innerHTML,/<script>/);
});

const pendingKey='session:mission-meme-cluster-pending-v1';
const pendingMint='33333333333333333333333333333333';
function setPending(h) {
  h.context.__id=secondJob;h.context.__mint=pendingMint;
  vm.runInContext('clusterSetJob(__id,__mint)',h.context);
  h.element('cluster-mint').value=pendingMint;
}
function deferred() {
  let resolve;
  const promise=new Promise(r=>{resolve=r;});
  return {promise,resolve};
}

test('reading saved A preserves pending B and resume reads B with its own CA',async()=>{
  const h=harness();await finish(h,jobId,'REPORT_A');setPending(h);
  const pending=h.store.get(pendingKey);
  h.element('cluster-reports').value=jobId;
  h.setResponse(async url=>({ok:true,status:200,json:async()=>
    url.startsWith('/api/cluster-analysis?') ? {job_id:jobId,mint,status:'DONE'} :
      {...fixture,ca_job_id:jobId,market:{...fixture.market,name:'REPORT_A'}}}));
  await h.element('cluster-read-report').listeners.get('click')();
  assert.match(h.element('cluster-summary').innerHTML,/REPORT_A/);
  assert.equal(h.store.get(pendingKey),pending);
  assert.equal(h.element('cluster-recovery').hidden,false);
  h.setResponse(async()=>({ok:true,status:200,json:async()=>({job_id:secondJob,mint:pendingMint,status:'RUNNING'})}));
  h.element('cluster-resume-get').listeners.get('click')();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.element('cluster-mint').value,pendingMint);
  assert.equal(h.requests.at(-1).url,'/api/cluster-analysis?job_id='+secondJob);
  assert.equal(h.requests.filter(x=>x.method==='POST').length,0);
});

test('failed saved A lookup leaves pending B recoverable',async()=>{
  const h=harness();await finish(h,jobId);setPending(h);
  const pending=h.store.get(pendingKey);
  h.element('cluster-reports').value=jobId;
  h.setResponse(async()=>({ok:false,status:404}));
  await h.element('cluster-read-report').listeners.get('click')();
  assert.equal(h.store.get(pendingKey),pending);
  assert.equal(h.element('cluster-recovery').hidden,false);
  assert.equal(h.element('cluster-result').hidden,true);
});

for (const control of ['cluster-read-cached','cluster-read-report']) {
  test(control+' during POST cannot discard its eventual acknowledged job',async()=>{
    const h=harness();await finish(h,jobId);
    const ack=deferred();
    h.setResponse(async(url,options)=>options.method==='POST' ? ack.promise :
      {ok:true,status:200,json:async()=>url.startsWith('/api/cluster-analysis?') ?
        {job_id:secondJob,mint:pendingMint,status:'RUNNING'} : {...fixture,ca_job_id:jobId}});
    h.element('cluster-mint').value=pendingMint;h.element('cluster-preset').value='quick';
    h.element('cluster-reports').value=jobId;
    const submitting=h.element('cluster-form').listeners.get('submit')({preventDefault(){}});
    const requestCount=h.requests.length;
    await h.element(control).listeners.get('click')();
    assert.equal(h.requests.length,requestCount,'no history GET while POST receipt is pending');
    ack.resolve({ok:true,status:202,json:async()=>({job_id:secondJob,mint:pendingMint})});
    await submitting;await new Promise(resolve=>setImmediate(resolve));
    assert.equal(JSON.parse(h.store.get(pendingKey)).id,secondJob);
    assert.equal(h.element('cluster-mint').value,pendingMint);
    assert.equal(h.requests.filter(x=>x.method==='POST').length,1);
  });
}

for (const wrong of [{ca_job_id:secondJob},{mint:pendingMint},{ca_job_id:undefined}]) {
  test('saved report rejects unverified server identity '+JSON.stringify(wrong),async()=>{
    const h=harness();await finish(h,jobId);setPending(h);
    const pending=h.store.get(pendingKey);
    h.element('cluster-reports').value=jobId;
    h.setResponse(async()=>({ok:true,status:200,json:async()=>({...fixture,ca_job_id:jobId,...wrong})}));
    await h.element('cluster-read-report').listeners.get('click')();
    assert.equal(h.element('cluster-result').hidden,true);
    assert.equal(h.store.get(pendingKey),pending);
    assert.match(h.element('cluster-status').innerHTML,/核对失败/);
  });
}

test('late saved report cannot overwrite the resumed pending task',async()=>{
  const h=harness();await finish(h,jobId);setPending(h);
  h.element('cluster-reports').value=jobId;
  const report=deferred();
  h.setResponse(async url=>url.startsWith('/api/cluster-latest?') ? report.promise :
    {ok:true,status:200,json:async()=>({job_id:secondJob,mint:pendingMint,status:'RUNNING'})});
  const loading=h.element('cluster-read-report').listeners.get('click')();
  h.element('cluster-resume-get').listeners.get('click')();
  await new Promise(resolve=>setImmediate(resolve));
  const status=h.element('cluster-status').innerHTML;
  report.resolve({ok:true,status:200,json:async()=>({...fixture,ca_job_id:jobId})});
  await loading;
  assert.equal(h.element('cluster-mint').value,pendingMint);
  assert.equal(h.element('cluster-result').hidden,true);
  assert.equal(h.element('cluster-status').innerHTML,status);
  assert.equal(JSON.parse(h.store.get(pendingKey)).id,secondJob);
});

test('failed POST unlocks history controls without automatically resubmitting',async()=>{
  const h=harness();await finish(h,jobId);
  h.element('cluster-preset').value='quick';
  h.setResponse(async()=>{throw new TypeError('lost POST response');});
  await h.element('cluster-form').listeners.get('submit')({preventDefault(){}});
  assert.equal(h.element('cluster-read-cached').disabled,false);
  assert.equal(h.element('cluster-read-report').disabled,false);
  assert.equal(h.requests.filter(x=>x.method==='POST').length,1);
  assert.match(h.element('cluster-status').innerHTML,/提交状态未核实/);
});

test('blocked localStorage reads do not prevent CA controls from initializing',()=>{
  const h=harness({storageReadError:true});
  assert.equal(typeof h.element('cluster-form').listeners.get('submit'),'function');
  assert.equal(typeof h.element('cluster-read-cached').listeners.get('click'),'function');
  assert.equal(h.element('cluster-read-report').disabled,true);
});

test('a failed optional last-CA write cannot discard an acknowledged POST job',async()=>{
  const h=harness({storageWriteError:true});
  h.element('cluster-mint').value=mint;h.element('cluster-preset').value='quick';
  h.setResponse(async(url,options)=>({ok:true,status:options.method==='POST'?202:200,json:async()=>
    options.method==='POST'?{job_id:jobId,mint}:{job_id:jobId,mint,status:'RUNNING'}}));
  await h.element('cluster-form').listeners.get('submit')({preventDefault(){}});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(JSON.parse(h.store.get(pendingKey)).id,jobId);
  assert.equal(h.requests.filter(x=>x.method==='POST').length,1);
  assert.equal(h.requests.at(-1).url,'/api/cluster-analysis?job_id='+jobId);
  assert.doesNotMatch(h.element('cluster-status').innerHTML,/提交状态未核实/);
});

test('an optional storage write failure after DONE keeps the received report successful',async()=>{
  const h=harness({storageWriteError:true});
  await finish(h,jobId,'REPORT_WITHOUT_STORAGE');
  assert.match(h.element('cluster-summary').innerHTML,/REPORT_WITHOUT_STORAGE/);
  assert.equal(h.store.has(pendingKey),false);
  assert.equal(h.element('cluster-submit').disabled,false);
  assert.match(h.element('cluster-status').innerHTML,/已读取该任务报告/);
  assert.doesNotMatch(h.element('cluster-status').innerHTML,/读取中断/);
});

test('editing CA while POST awaits receipt cannot mislabel its acknowledged job',async()=>{
  const h=harness(),ack=deferred();
  h.setResponse(async(url,options)=>options.method==='POST'?ack.promise:
    {ok:true,status:200,json:async()=>({job_id:jobId,mint,status:'RUNNING'})});
  h.element('cluster-mint').value=mint;h.element('cluster-preset').value='quick';
  const submitting=h.element('cluster-form').listeners.get('submit')({preventDefault(){}});
  h.element('cluster-mint').value=pendingMint;
  ack.resolve({ok:true,status:202,json:async()=>({job_id:jobId,mint})});
  await submitting;await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.element('cluster-mint').value,mint);
  assert.equal(JSON.parse(h.store.get(pendingKey)).mint,mint);
});

test('editing CA during historical GET still exposes the paused pending task',async()=>{
  const h=harness(),report=deferred();
  setPending(h);
  h.element('cluster-submit').disabled=true;
  h.setResponse(async()=>report.promise);
  const loading=h.element('cluster-read-cached').listeners.get('click')();
  h.element('cluster-mint').value=mint;
  report.resolve({ok:true,status:200,json:async()=>({...fixture,mint:pendingMint})});
  await loading;
  assert.equal(h.element('cluster-recovery').hidden,false);
  assert.equal(h.element('cluster-resume-get').hidden,false);
  assert.equal(JSON.parse(h.store.get(pendingKey)).id,secondJob);
  assert.equal(h.requests.filter(x=>x.method==='POST').length,0);
});


for(const action of ['history-invalid-ca','submit-invalid-ca','submit-invalid-mode']){
  test(action+' hides prior report/preview without a request or losing pending identity',async()=>{
    const h=harness();
    setPending(h);
    h.context.renderClusterReport({...fixture,ca_job_id:jobId});
    h.element('cluster-preview').hidden=false;
    assert.equal(h.element('cluster-result').hidden,false);
    const pending=h.store.get(pendingKey),requests=h.requests.length;
    h.element('cluster-mint').value=action==='submit-invalid-mode'?mint:'bad CA';
    h.element('cluster-preset').value=action==='submit-invalid-mode'?'unsupported':'quick';
    if(action==='history-invalid-ca')await h.element('cluster-read-cached').listeners.get('click')();
    else await h.element('cluster-form').listeners.get('submit')({preventDefault(){}});
    assert.equal(h.element('cluster-result').hidden,true);
    assert.equal(h.element('cluster-preview').hidden,true);
    assert.equal(h.store.get(pendingKey),pending);
    assert.equal(h.requests.length,requests);
    assert.match(h.element('cluster-status').innerHTML,/请输入完整|请选择有效/);
  });
}

async function readGetFixture(h,path) {
  h.context.__getPath=path;
  return await vm.runInContext('get(__getPath)',h.context,{timeout:2500});
}

for (const endpoint of ['/api/runtime','/api/control-health','/api/candidates','/api/follow-opportunities']) {
  test('GET network failure identifies '+endpoint+' without leaking exception details or retrying',async()=>{
    const h=harness(),before=h.requests.length;
    h.setResponse(async()=>{throw new TypeError('private-fixture-origin?token=fixture-secret');});
    await assert.rejects(()=>readGetFixture(h,endpoint+'?mint=fixture-mint&job_id=fixture-job'),error=>{
      assert.match(error.message,/\[NETWORK\]/);
      assert.ok(error.message.includes(endpoint));
      assert.doesNotMatch(error.message,/private-fixture|fixture-secret|fixture-mint|fixture-job|token=|job_id=/);
      return true;
    });
    assert.equal(h.requests.length,before+1);
    assert.equal(h.requests.at(-1).method,'GET');
  });
}

test('GET JSON failure identifies the decode stage without exposing response contents',async()=>{
  const h=harness(),before=h.requests.length;
  let jsonReads=0;
  h.setResponse(async()=>({ok:true,status:200,json:async()=>{
    jsonReads++;throw new SyntaxError('private JSON body with fixture-secret');
  }}));
  await assert.rejects(()=>readGetFixture(h,'/api/candidates?mint=fixture-mint'),error=>{
    assert.match(error.message,/GET \/api\/candidates 200 \[JSON\]/);
    assert.doesNotMatch(error.message,/private JSON|fixture-secret|fixture-mint|SyntaxError/);
    return true;
  });
  assert.equal(jsonReads,1);
  assert.equal(h.requests.length,before+1);
});

test('GET HTTP 404 retains the CA terminal-status contract and does not read error body',async()=>{
  const h=harness(),before=h.requests.length;
  let jsonReads=0;
  h.setResponse(async()=>({ok:false,status:404,json:async()=>{jsonReads++;throw Error('private body');}}));
  await assert.rejects(()=>readGetFixture(h,'/api/cluster-analysis?job_id='+jobId),error=>{
    assert.match(error.message,/GET \/api\/cluster-analysis 404 \[HTTP\]/);
    assert.ok(error.message.includes(' 404'));
    assert.doesNotMatch(error.message,new RegExp(jobId));
    return true;
  });
  assert.equal(jsonReads,0);
  assert.equal(h.requests.length,before+1);
});

test('GET failure never echoes an unrecognized URL or its private query',async()=>{
  const h=harness();
  h.setResponse(async()=>{throw Error('fixture-secret');});
  await assert.rejects(()=>readGetFixture(h,'https://private-fixture.invalid/path?token=fixture-secret'),error=>{
    assert.match(error.message,/\[NETWORK\]/);
    assert.doesNotMatch(error.message,/private-fixture|fixture-secret|https:|token=/);
    return true;
  });
});

test('GET success returns the unchanged payload with one fetch and one JSON read',async()=>{
  const h=harness(),before=h.requests.length,payload={rows:[{value:'fixture'}]};
  let jsonReads=0;
  h.setResponse(async()=>({ok:true,status:200,json:async()=>{jsonReads++;return payload;}}));
  assert.equal(await readGetFixture(h,'/api/candidates'),payload);
  assert.equal(jsonReads,1);
  assert.equal(h.requests.length,before+1);
});

const observedPanelConfigs=[
  {kind:'intelligence',refresh:'refreshFrankIntelligence',endpoint:'/api/frank-intelligence',
   root:'frank-intelligence-cards',summary:'frank-intelligence-summary',updated:'frank-intelligence-updated',
   filter:'frank-intelligence-search',status:'LOCAL_SOURCE_RESEARCH_ONLY'},
  {kind:'activity',refresh:'refreshFrankActivity',endpoint:'/api/frank-activity-watch',
   root:'frank-activity-feed',summary:'frank-activity-summary',updated:'frank-activity-updated',
   filter:'frank-activity-search',status:'LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY'},
];
function observedPayload(config,target,side='SELL') {
  const row=config.kind==='intelligence'
    ? {mint:target,latest_side:side,latest_action_at:1,source_signal_id:'FIXTURE_'+side,
       facts:side==='SELL'?['FRANK_SELL_OBSERVED_REVIEW_RISK']:[],missing:[],price:{}}
    : {mint:target,source_side:side,signature:'5'.repeat(64),block_time:1};
  return {status:config.status,rows:[row],source_rows_considered:1,counts:{}};
}
function invokeObserved(h,config) {
  return vm.runInContext(config.refresh+'()',h.context,{timeout:2500});
}
function observedHarness(config) {
  const h=harness();
  h.element('frank-activity-type').value='ALL';
  return h;
}
for (const config of observedPanelConfigs) {
  const newerMint='3'.repeat(32);
  test(config.kind+': delayed older BUY cannot overwrite the newer SELL response or filtering snapshot',async()=>{
    const h=observedHarness(config),old=deferred();
    let calls=0;
    h.setResponse(async()=>++calls===1?old.promise:
      {ok:true,status:200,json:async()=>observedPayload(config,newerMint)});
    const pending=invokeObserved(h,config);
    await invokeObserved(h,config);
    assert.ok(h.element(config.root).innerHTML.includes(newerMint));
    old.resolve({ok:true,status:200,json:async()=>observedPayload(config,mint,'BUY')});
    await pending;
    assert.ok(h.element(config.root).innerHTML.includes(newerMint));
    assert.ok(!h.element(config.root).innerHTML.includes(mint));
    h.element(config.filter).listeners.get('input')();
    assert.ok(h.element(config.root).innerHTML.includes(newerMint));
    assert.equal(h.requests.filter(x=>x.method==='POST').length,0);
  });
  test(config.kind+': late old success cannot resurrect rows after the latest GET failure',async()=>{
    const h=observedHarness(config),old=deferred();
    let calls=0;
    h.setResponse(async()=>{
      if(++calls===1)return old.promise;
      throw new TypeError('fixture connection failure');
    });
    const pending=invokeObserved(h,config);
    await invokeObserved(h,config);
    assert.equal(h.element(config.updated).textContent,'来源不可用');
    old.resolve({ok:true,status:200,json:async()=>observedPayload(config,mint,'BUY')});
    await pending;
    assert.equal(h.element(config.updated).textContent,'来源不可用');
    assert.ok(!h.element(config.root).innerHTML.includes(mint));
  });
  test(config.kind+': late old failure cannot clear a newer successful response',async()=>{
    const h=observedHarness(config),old=deferred();
    let calls=0;
    h.setResponse(async()=>++calls===1?old.promise:
      {ok:true,status:200,json:async()=>observedPayload(config,newerMint)});
    const pending=invokeObserved(h,config);
    await invokeObserved(h,config);
    old.reject(new TypeError('old fixture failure'));
    await pending;
    assert.ok(h.element(config.root).innerHTML.includes(newerMint));
    assert.notEqual(h.element(config.updated).textContent,'来源不可用');
  });
  test(config.kind+': filter after a failed refresh cannot restore a last-good snapshot',async()=>{
    const h=observedHarness(config);
    h.element('frank-d2-rows').innerHTML='KEEP_D2';
    h.element('cluster-status').innerHTML='KEEP_CA';
    h.setResponse(async()=>({ok:true,status:200,json:async()=>observedPayload(config,mint,'BUY')}));
    await invokeObserved(h,config);
    assert.ok(h.element(config.root).innerHTML.includes(mint));
    h.setResponse(async()=>{throw new TypeError('fixture failure');});
    await invokeObserved(h,config);
    h.element(config.filter).listeners.get('input')();
    assert.ok(!h.element(config.root).innerHTML.includes(mint));
    assert.equal(h.element(config.updated).textContent,'来源不可用');
    assert.equal(h.element('frank-d2-rows').innerHTML,'KEEP_D2');
    assert.equal(h.element('cluster-status').innerHTML,'KEEP_CA');
  });
  test(config.kind+': a subsequent successful GET restores normal rendering after a failure',async()=>{
    const h=observedHarness(config);
    h.setResponse(async()=>{throw new TypeError('fixture failure');});
    await invokeObserved(h,config);
    h.setResponse(async()=>({ok:true,status:200,json:async()=>observedPayload(config,newerMint)}));
    await invokeObserved(h,config);
    assert.ok(h.element(config.root).innerHTML.includes(newerMint));
    assert.notEqual(h.element(config.updated).textContent,'来源不可用');
    assert.equal(h.requests.filter(x=>x.method==='POST').length,0);
  });
}
