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
  let resolve, reject;
  const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});
  return {promise,resolve,reject};
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


for(const action of ['history-invalid-ca','submit-invalid-ca']){
  test(action+' hides prior report/preview without a request or losing pending identity',async()=>{
    const h=harness();
    setPending(h);
    h.context.renderClusterReport({...fixture,ca_job_id:jobId});
    h.element('cluster-preview').hidden=false;
    assert.equal(h.element('cluster-result').hidden,false);
    const pending=h.store.get(pendingKey),requests=h.requests.length;
    h.element('cluster-mint').value='bad CA';
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


test('CA legacy normalization flag cannot expose exact metrics without ranks and slots',()=>{
  const h=harness();
  h.context.renderClusterReport({...fixture,market:{...fixture.market,status:'OK'},coverage:{special_normalization_complete:true},metrics:{EX_LP_TOP10_PCT:'98.7654',DEV_LINKED_CLUSTER_PCT:'87.6543',KNOWN_EX_LP_TOP10_PCT:'12.34'}});
  const metrics=h.element('cluster-metrics').innerHTML;
  assert.ok(!metrics.includes('98.7654'));
  assert.ok(!metrics.includes('87.6543'));
  assert.match(metrics,/已解析样本/);
  assert.match(metrics,/12.34/);
  assert.match(h.element('cluster-coverage').innerHTML,/完整持有人排名/);
  assert.match(h.element('cluster-coverage').innerHTML,/同一 slot/);
});

test('CA exact concentration remains available with verified labels ranks and slots',()=>{
  const h=harness();
  h.context.renderClusterReport({...fixture,coverage:{special_normalization_complete:true,eligible_owner_rank_complete:true,snapshot_consistent:true},metrics:{EX_LP_TOP10_PCT:'42.1234',DEV_LINKED_CLUSTER_PCT:'12.1234'}});
  assert.match(h.element('cluster-metrics').innerHTML,/42.1234/);
  assert.match(h.element('cluster-metrics').innerHTML,/12.1234/);
});

test('CA coverage shows specific bounded gaps without echoing untrusted codes',()=>{
  const h=harness();
  h.context.renderClusterReport({...fixture,coverage:{...fixture.coverage,gaps:['OWNER_HISTORY_NOT_SCANNED','TOP_ACCOUNT_RESOLUTION_GAPS','MULTIPLE_TOKEN_ACCOUNTS_PER_OWNER','TRANSACTION_READ_GAPS','http://private.example/SECRET']}});
  const coverage=h.element('cluster-coverage').innerHTML;
  assert.match(coverage,/部分钱包历史尚未扫描/);
  assert.match(coverage,/部分 Top20 账户尚未解析/);
  assert.match(coverage,/同一钱包存在多个代币账户/);
  assert.match(coverage,/历史交易存在读取缺口/);
  assert.ok(!coverage.includes('SECRET'));
});



test('CA has one visible query entry and no accuracy preset selector',()=>{
  const html=readFileSync(new URL('../mission_agent/mission_control/static/index.html',import.meta.url),'utf8');
  assert.doesNotMatch(html,/id="cluster-preset"|title="扫描深度"/);
  assert.match(html,/统一查询/);
});

test('CA submit uses fixed bounded standard without reading a mode control',async()=>{
  let posted;
  const h=harness({responseFor:async(url,options)=>{
    if(options.method==='POST'){
      posted=JSON.parse(options.body);
      return {ok:false,status:400,json:async()=>({error:'FIXTURE_DENIED'})};
    }
    return new Promise(()=>{});
  }});
  h.element('cluster-mint').value=mint;
  h.element('cluster-preset').value='unsupported-stale-dom';
  await h.element('cluster-form').listeners.get('submit')({preventDefault(){}});
  assert.deepEqual(posted,{mint,preset:'standard'});
  assert.equal(h.requests.filter(x=>x.method==='POST').length,1);
});


test('CA report exposes per-address page window, bound and continuation without completeness claim',()=>{
  const h=harness();
  h.context.renderClusterReport({...fixture,coverage:{...fixture.coverage,holder_history_pages:4,funding_history_pages:5,gaps:['HISTORY_PAGINATION_INCOMPLETE'],history_windows:[{owner:mint,address:mint,phase:'holder',page_size:30,pages:4,signature_count:120,oldest_block_time:1792683606,next_before:'public-cursor',stop_reason:'PAGE_LIMIT',history_complete:false}]}});
  const html=h.element('cluster-coverage').innerHTML;
  assert.match(html,/目标币账户历史/);
  assert.match(html,/120/);
  assert.match(html,/达到本轮页数上限/);
  assert.match(html,/分页游标/);
  assert.match(html,/来源空页也不证明完整钱包历史/);
});

test('CA history progress and unknown stop reason never echo raw provider errors',()=>{
  const h=harness();
  assert.match(h.context.clusterProgressDetail({progress:{stage:'HISTORY_PAGE',phase:'holder',pages:2,signature_count:60}}),/历史分页/);
  h.context.renderClusterReport({...fixture,coverage:{...fixture.coverage,history_windows:[{owner:mint,phase:'holder',pages:1,stop_reason:'https://private.invalid/SECRET'}]}});
  assert.ok(!h.element('cluster-coverage').innerHTML.includes('SECRET'));
});


test('full mint Owner rank is separate from raw Top20 account history and unavailable legacy ranks hide',()=>{
  const h=harness();
  h.context.renderClusterReport({...fixture,coverage:{...fixture.coverage,special_normalization_complete:true,snapshot_consistent:true,eligible_owner_rank_complete:true,sample_owner_rank_complete:false},metrics:{EX_LP_TOP10_PCT:'99.8765'},holder_rankings:{requested:true,status:'COMPLETE_SNAPSHOT',snapshot_slot:100,supply_slot:100,account_count:30,nonzero_owner_count:11,normalization_complete:true,metrics:{GLOBAL_OWNER_TOP10_PCT:'98.0000',GLOBAL_EX_LP_OWNER_TOP10_PCT:'20.0000'},owners:[{owner:mint,raw:'800',account_count:20,role:'LP',supply_pct:'80.0000',history_scanned:false}],decimals:0}});
  assert.equal(h.element('cluster-rankings-panel').hidden,false);
  const html=h.element('cluster-rankings').innerHTML;
  assert.match(html,/全局 Owner Top10/);
  assert.match(html,/98%/);
  assert.match(html,/20%/);
  assert.match(html,/30/);
  assert.match(html,/本轮未覆盖历史/);
  assert.ok(!h.element('cluster-metrics').innerHTML.includes('99.8765'));
  h.context.renderClusterReport(fixture);
  assert.equal(h.element('cluster-rankings-panel').hidden,true);
});

test('incomplete global snapshot masks exact metrics and maps safe source reason',()=>{
  const h=harness();
  h.context.renderClusterReport({...fixture,holder_rankings:{requested:true,status:'INCOMPLETE_EVIDENCE',reason:'SUPPLY_SUM_MISMATCH',metrics:{GLOBAL_OWNER_TOP10_PCT:'99.8765'},owners:[]}});
  assert.match(h.element('cluster-rankings').innerHTML,/余额总和与供给未对上/);
  assert.ok(!h.element('cluster-rankings').innerHTML.includes('99.8765'));
  h.context.renderClusterReport({...fixture,holder_rankings:{requested:true,status:'UNAVAILABLE',reason:'https://private.invalid/SECRET',owners:[]}});
  assert.ok(!h.element('cluster-rankings').innerHTML.includes('SECRET'));
});

test('complete holder flags and PASS permissions never imply complete analysis',()=>{
  const h=harness();
  const report=structuredClone(fixture);
  Object.assign(report.coverage,{special_normalization_complete:true,eligible_owner_rank_complete:true,sample_owner_rank_complete:true,snapshot_consistent:true,gaps:[]});
  report.assessment.chain_permission_status='PASS';
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  assert.match(h.element('cluster-completeness').innerHTML,/完整性尚未评估/);
  assert.doesNotMatch(h.element('cluster-status').className,/done/);
});

test('explicit incomplete contract displays mandatory gaps despite complete rank snapshot',()=>{
  const h=harness();const report=structuredClone(fixture);
  report.analysis_completeness={version:1,status:'INCOMPLETE_EVIDENCE',requirements:[
    {id:'holder_balances',status:'VERIFIED_SNAPSHOT'},
    {id:'wallet_history',status:'PARTIAL'},
    {id:'narrative',status:'NOT_COLLECTED'},
    {id:'independent_sources',status:'NOT_COLLECTED'},
  ]};
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  const html=h.element('cluster-completeness').innerHTML;
  assert.match(html,/证据不完整/);assert.match(html,/完整历史/);assert.match(html,/外部叙事/);
  assert.match(html,/独立来源/);assert.match(html,/下一来源/);
  assert.match(h.element('cluster-status').innerHTML,/证据不完整/);
});

test('unsupported complete claims and source text cannot turn completeness green or inject markup',()=>{
  const h=harness();const report=structuredClone(fixture);
  report.analysis_completeness={version:1,status:'ANALYSIS_COMPLETE',requirements:[{id:'<img src=x onerror=alert(1)>',status:'VERIFIED_SNAPSHOT',cause:'SECRET_PROVIDER_TEXT'}]};
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  assert.match(h.element('cluster-completeness').innerHTML,/完整性状态无法核实/);
  assert.doesNotMatch(h.element('cluster-completeness').innerHTML,/<img|SECRET_PROVIDER_TEXT/);
  assert.doesNotMatch(h.element('cluster-status').className,/done/);
});

test('owner multi-account history shows each selected address and never claims lifetime completion',()=>{
  const h=harness();const report=structuredClone(fixture);
  report.coverage.owner_account_history=[{owner:mint,account_source_status:'VERIFIED_CURRENT_MINT_ACCOUNTS',current_accounts_observed:3,accounts_selected:['11111111111111111111111111111112','11111111111111111111111111111113'],accounts_with_windows:['11111111111111111111111111111112','11111111111111111111111111111113'],accounts_not_selected:1,account_selection_complete:false,selection_stop_reason:'REPORT_EXTRA_ACCOUNT_LIMIT',history_complete:false}];
  report.coverage.history_windows=[{owner:mint,address:'11111111111111111111111111111113',phase:'holder',pages:1,signature_count:1,page_size:12,stop_reason:'PAGE_LIMIT'}];
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  const html=h.element('cluster-coverage').innerHTML;
  assert.match(html,/Owner 逐账户历史覆盖/);
  assert.match(html,/11111111111111111111111111111113/);
  assert.match(html,/本轮额外账户上限/);
  assert.match(html,/已关闭账户.*未枚举/);
  assert.match(html,/不证明完整经济历史/);
});

test('verified current account selection and source empty pages do not turn history complete',()=>{
  const h=harness();const report=structuredClone(fixture);
  report.coverage.owner_account_history=[{owner:mint,account_source_status:'VERIFIED_CURRENT_MINT_ACCOUNTS',current_accounts_observed:1,accounts_selected:[mint],accounts_with_windows:[mint],accounts_not_selected:0,account_selection_complete:true,selection_stop_reason:'ALL_OBSERVED_SELECTED',history_complete:false}];
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  assert.match(h.element('cluster-coverage').innerHTML,/当前来源账户均已选择/);
  assert.match(h.element('cluster-coverage').innerHTML,/不证明完整经济历史/);
  report.coverage={};
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  assert.doesNotMatch(h.element('cluster-coverage').innerHTML,/当前来源账户均已选择/);
});

test('historical account proof keeps phase, close-at-transaction time and unscanned frontier visible',()=>{
  const h=harness();const report=structuredClone(fixture);
  report.historical_account_evidence=[{owner:mint,account:'11111111111111111111111111111112',signature:'PROOF_SIGNATURE',slot:100,block_time:1000,raw:'10',decimals:0,balance_phase:'pre',closure_at_transaction_end:'CONFIRMED_CLOSED_AT_TRANSACTION_END',response_sha256:'a'.repeat(64)}];
  report.coverage.historical_account_history=[{owner:mint,account:'11111111111111111111111111111112',selected:false,stop_reason:'FRONTIER_LIMIT'}];
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  const html=h.element('cluster-coverage').innerHTML;
  assert.match(html,/交易前余额/);assert.match(html,/该交易结束时关闭/);
  assert.match(html,/PROOF_SIGNATURE/);assert.match(html,/本轮只补查一轮/);
  assert.match(html,/不能证明当前仍关闭/);
  report.historical_account_evidence=[];report.coverage={};
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  assert.doesNotMatch(h.element('cluster-coverage').innerHTML,/该交易结束时关闭<\/td>|PROOF_SIGNATURE/);
  assert.match(h.element('cluster-coverage').innerHTML,/本轮没有可核实/);
});

test('missing historical proof context never upgrades a close string to confirmed current closure',()=>{
  const h=harness();const report=structuredClone(fixture);
  report.historical_account_evidence=[{owner:mint,account:mint,closure_at_transaction_end:'CONFIRMED_CLOSED_AT_TRANSACTION_END',balance_phase:'pre',signature:'<script>bad</script>'}];
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  const html=h.element('cluster-coverage').innerHTML;
  assert.match(html,/关闭状态未证明/);
  assert.doesNotMatch(html,/<script>|该交易结束时关闭<\/td>/);
});

test('market comparison displays same-pool source values and differences without a parity PASS',()=>{
  const h=harness();const report=structuredClone(fixture);const pool='11111111111111111111111111111112',quote='11111111111111111111111111111113';
  report.market={status:'OK',mint,source:'DEXSCREENER_API',observed_at:100,price_usd:'2',main_pair:{pair_address:pool,base_address:mint,quote_address:quote,liquidity_usd:'1000'},independent_market:{status:'OK',source:'GECKOTERMINAL_PUBLIC_API',attempted:true,pool_address:pool,mint,quote_address:quote,observed_at:102},comparison:{status:'INDEXER_SNAPSHOTS_COMPARED',pool_address:pool,mint,quote_address:quote,retrieval_gap_seconds:2,same_chain_snapshot:false,provider_asof:'UNVERIFIED',metrics:{price_usd:{status:'COMPARED',primary:'2',independent:'2.5',difference:'0.5',difference_pct_of_primary:'25.0000'},pool_liquidity_usd:{status:'COMPARED',primary:'1000',independent:'900',difference:'-100',difference_pct_of_primary:'-10.0000'}}}};
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  const html=h.element('cluster-market').innerHTML;
  assert.match(html,/GeckoTerminal/);assert.match(html,/25.0000%/);assert.match(html,/-10.0000%/);
  assert.match(html,/读取时间.*行情观测时间/);assert.match(html,/未核对链上池子储备/);
  assert.doesNotMatch(html,/PARITY_PASS|交叉验证通过/);
  report.market={status:'UNAVAILABLE',independent_market:{status:'UNAVAILABLE',attempted:true,reason:'SECRET_PROVIDER_TEXT'},comparison:{status:'INCOMPLETE_EVIDENCE',metrics:{}}};
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  assert.doesNotMatch(h.element('cluster-market').innerHTML,/25.0000%|SECRET_PROVIDER_TEXT/);
});

test('mismatched comparison identity masks metrics even when its status claims compared',()=>{
  const h=harness();const report=structuredClone(fixture);
  report.market={status:'OK',main_pair:{pair_address:mint},independent_market:{status:'OK'},comparison:{status:'INDEXER_SNAPSHOTS_COMPARED',mint:'OTHER',pool_address:'OTHER',metrics:{price_usd:{status:'COMPARED',primary:'2',independent:'2.5',difference_pct_of_primary:'999.1234'}}}};
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  assert.match(h.element('cluster-market').innerHTML,/独立来源身份未核实/);
  assert.doesNotMatch(h.element('cluster-market').innerHTML,/999.1234/);
});

test('external page claims remain readable without exact CA recognition and escape publisher markup',()=>{
  const h=harness();const report=structuredClone(fixture);
  report.narrative={version:1,status:'PARTIAL',official_recognition:'VERIFIED',exhaustive:false,search_coverage:'BOUNDED_HINTS_ONLY',evidence:[{classification:'THIRD_PARTY_CLAIM',source_url:'https://project.example.org/about',publisher_host:'project.example.org',title:'Fixture story',excerpt:'A cat explores distant planets <img onerror=bad>',exact_ca_mentioned:false,published_at_claim:null,first_seen_at:100,response_sha256:'a'.repeat(64)}],attempts:[{kind:'LAUNCHPAD_PAGE',source_url:'https://pump.fun/coin/'+mint,status:'UNAVAILABLE',reason:'HTTP_403',requested:true}]};
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  const html=h.element('cluster-narrative').innerHTML;
  assert.match(html,/A cat explores/);assert.match(html,/精确 CA 未提及/);
  assert.match(html,/官方归属未核实/);assert.match(html,/本报告首次读取/);
  assert.match(html,/403/);assert.match(html,/未做全网检索/);
  assert.doesNotMatch(html,/<img|认领已核实/);
});

test('reading legacy report removes prior external claim and does not fabricate source attempts',()=>{
  const h=harness();const report=structuredClone(fixture);
  report.narrative={version:1,status:'PARTIAL',evidence:[{classification:'THIRD_PARTY_CLAIM',source_url:'https://project.example.org/',excerpt:'UNIQUE_OLD_NARRATIVE',response_sha256:'a'.repeat(64)}],attempts:[]};
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:report}));
  assert.match(h.element('cluster-narrative').innerHTML,/UNIQUE_OLD_NARRATIVE/);
  vm.runInContext('renderClusterReport(__report)',Object.assign(h.context,{__report:fixture}));
  assert.doesNotMatch(h.element('cluster-narrative').innerHTML,/UNIQUE_OLD_NARRATIVE/);
  assert.match(h.element('cluster-narrative').innerHTML,/历史报告.*未记录外部来源读取/);
});

test('raw vault balances show actual batch slot and precision while prices remain unverified',()=>{
  const h=harness(),pool='POOL',quote='QUOTE';
  const r={...fixture,market:{status:'OK',source:'DEXSCREENER_API',mint,main_pair:{pair_address:pool,base_address:mint,quote_address:quote}},pool_vaults:{status:'VAULT_BALANCE_SNAPSHOT',mint,pool_address:pool,snapshot_slot:101,discovery_slot:100,raw_vault_quote_per_target:'2',target:{mint,vault:'A',authority:pool,raw:'100',decimals:6,quantity:'0.000100'},quote:{mint:quote,vault:'B',authority:pool,raw:'200',decimals:6,quantity:'0.000200'},flags:['<unsafe>']}};
  h.context.renderClusterReport(r);
  let html=h.element('cluster-market').innerHTML;
  assert.match(html,/finalized slot 101/);assert.match(html,/0.000100/);assert.match(html,/不作为市场价格/);
  assert.match(html,/美元价格、美元流动性、可执行报价与索引同快照对齐均未核实/);assert.doesNotMatch(html,/<unsafe>/);
  r.pool_vaults.pool_address='WRONG';h.context.renderClusterReport(r);html=h.element('cluster-market').innerHTML;
  assert.doesNotMatch(html,/0.000100|finalized slot 101/);assert.match(html,/证据不完整/);
});

test('unsupported raw pool never displays provider exception text or old balance rows',()=>{
  const h=harness();h.context.renderClusterReport({...fixture,pool_vaults:{status:'UNSUPPORTED',reason:'UNSUPPORTED_POOL_PROGRAM'}});
  assert.match(h.element('cluster-market').innerHTML,/未读取其他池子/);
  h.context.renderClusterReport({...fixture,pool_vaults:{status:'INCOMPLETE_EVIDENCE',reason:'SECRET_RAW_ERROR'}});
  assert.doesNotMatch(h.element('cluster-market').innerHTML,/SECRET_RAW_ERROR/);
});

function reserveReportForUi() {
  const pool='POOL',quote='QUOTE';
  return {...fixture,market:{status:'OK',source:'DEXSCREENER_API',mint,main_pair:{pair_address:pool,base_address:mint,quote_address:quote}},pool_vaults:{status:'VAULT_BALANCE_SNAPSHOT',mint,pool_address:pool,snapshot_slot:101,discovery_slot:100,raw_vault_quote_per_target:'2',target:{mint,vault:'A',authority:pool,raw:'100',decimals:0,quantity:'100'},quote:{mint:quote,vault:'B',authority:pool,raw:'200',decimals:0,quantity:'200'},flags:[],effective_reserves:{version:1,status:'DERIVED_PROTOCOL_RESERVES',formula:'PUMPSWAP_SIGNED_VQR_V1',protocol_base_mint:mint,protocol_quote_mint:quote,target_mint:mint,quote_mint:quote,base_decimals:0,quote_decimals:0,base_raw:'100',base_quantity:'100',quote_vault_raw:'200',quote_vault_quantity:'200',waiting_fees_raw:'15',waiting_fees_quantity:'15',virtual_quote_raw:'-15',real_quote_raw:'185',real_quote_quantity:'185',effective_quote_raw:'185',effective_quote_quantity:'185',boost_component_raw:'0',boost_component_quantity:'0',effective_quote_per_target:'1.85',documented_zero_defaults:[],deployed_binary_semantics:'UNVERIFIED'}}};
}

test('signed protocol reserve model is separate from raw balance and excludes waiting fees once',()=>{
  const h=harness(),report=reserveReportForUi();h.context.renderClusterReport(report);
  const html=h.element('cluster-market').innerHTML;
  assert.match(html,/cluster-pool-reserves/);assert.match(html,/有效储备 = 金库余额 \+ 有符号虚拟储备/);
  assert.match(html,/-15/);assert.match(html,/185/);assert.match(html,/1.85/);
  assert.match(html,/不再重复减去待提取费用/);assert.match(html,/美元价格、美元流动性、可执行报价与索引同快照对齐均未核实/);
  assert.match(html,/已部署程序二进制/);
});

test('legacy reports and inconsistent or unsupported reserve models never inherit a computed ratio',()=>{
  const h=harness(),report=reserveReportForUi();h.context.renderClusterReport(report);
  report.pool_vaults.effective_reserves.status='INCOMPLETE_EVIDENCE';report.pool_vaults.effective_reserves.reason='SECRET';
  h.context.renderClusterReport(report);assert.doesNotMatch(h.element('cluster-market').innerHTML,/1.85|SECRET/);
  delete report.pool_vaults.effective_reserves;h.context.renderClusterReport(report);
  assert.match(h.element('cluster-market').innerHTML,/此报告未计算协议储备/);assert.doesNotMatch(h.element('cluster-market').innerHTML,/1.85/);
  report.pool_vaults.effective_reserves=reserveReportForUi().pool_vaults.effective_reserves;
  report.pool_vaults.effective_reserves.protocol_quote_mint='WRONG';h.context.renderClusterReport(report);
  assert.doesNotMatch(h.element('cluster-market').innerHTML,/1.85|185/);
});

test('documented default zeros are identified and Token-2022 arithmetic does not display a ratio',()=>{
  const h=harness(),report=reserveReportForUi();report.pool_vaults.effective_reserves.documented_zero_defaults=['virtual_quote_reserves'];
  report.pool_vaults.effective_reserves.status='ARITHMETIC_ONLY';report.pool_vaults.effective_reserves.ratio_reason='TOKEN_ECONOMICS_UNVERIFIED';
  report.pool_vaults.effective_reserves.effective_quote_per_target='UNRESOLVED';h.context.renderClusterReport(report);
  const html=h.element('cluster-market').innerHTML;
  assert.match(html,/文档约定的零默认值/);assert.match(html,/Token-2022 或冻结状态/);assert.doesNotMatch(html,/1.85/);
});

test('reserve model rejects inconsistent arithmetic and preserves reversed protocol direction',()=>{
  const h=harness(),report=reserveReportForUi(),m=report.pool_vaults.effective_reserves;
  m.effective_quote_raw='170';h.context.renderClusterReport(report);assert.doesNotMatch(h.element('cluster-market').innerHTML,/1.85|185/);
  m.effective_quote_raw='185';m.protocol_base_mint='QUOTE';m.protocol_quote_mint=mint;
  m.base_raw='200';m.quote_vault_raw='100';m.waiting_fees_raw='10';m.virtual_quote_raw='-10';m.real_quote_raw='90';m.effective_quote_raw='90';m.boost_component_raw='0';m.effective_quote_per_target='2.2222222222';
  h.context.renderClusterReport(report);assert.match(h.element('cluster-market').innerHTML,/2.2222222222/);
});

function unitRatioReportForUi() {
  const r=reserveReportForUi(),pool=r.pool_vaults,m=r.pool_vaults.effective_reserves;
  pool.response_sha256='a'.repeat(64);pool.observed_at=103;
  r.market.independent_market={status:'OK',attempted:true,observed_at:101,source:'GECKOTERMINAL_PUBLIC_API',mint,quote_address:'QUOTE',pool_address:'POOL',target_orientation:'BASE',price_quote_units:'1.9',price_quote_units_field:'base_token_price_quote_token',response_sha256:'b'.repeat(64)};
  pool.market_comparison={version:1,status:'UNALIGNED_RATIO_COMPARISON',mint,quote_address:'QUOTE',pool_address:'POOL',model_quote_per_target:m.effective_quote_per_target,indexer_quote_per_target:'1.9',indexer_field:'base_token_price_quote_token',snapshot_slot:101,same_chain_snapshot:false,provider_asof:'UNVERIFIED',price_basis_alignment:'UNVERIFIED',chain_response_sha256:'a'.repeat(64),indexer_response_sha256:'b'.repeat(64),chain_result_received_at:103,indexer_result_received_at:101,retrieval_gap_seconds:2,difference_indexer_minus_model:'0.05',difference_pct_of_model:'2.7027'};
  return r;
}

test('pool and indexer ratio comparison preserves explicit units and unaligned timing',()=>{
  const h=harness();h.context.renderClusterReport(unitRatioReportForUi());const html=h.element('cluster-market').innerHTML;
  assert.match(html,/cluster-pool-ratio-comparison/);assert.match(html,/1.9/);assert.match(html,/0.05/);assert.match(html,/2.7027%/);
  assert.match(html,/QUOTE \/ 222222/);assert.match(html,/相同数值也不能证明同一行情快照/);
  assert.match(html,/读取结果可能来自缓存/);assert.match(html,/美元估值和可执行报价未核实/);
});

test('ratio comparison clears mismatched identities, forged alignment and legacy report values',()=>{
  const h=harness(),r=unitRatioReportForUi();h.context.renderClusterReport(r);
  r.pool_vaults.market_comparison.pool_address='WRONG';h.context.renderClusterReport(r);
  assert.doesNotMatch(h.element('cluster-market').innerHTML,/2.7027%/);
  r.pool_vaults.market_comparison=unitRatioReportForUi().pool_vaults.market_comparison;
  r.pool_vaults.market_comparison.same_chain_snapshot=true;h.context.renderClusterReport(r);
  assert.doesNotMatch(h.element('cluster-market').innerHTML,/2.7027%/);
  delete r.pool_vaults.market_comparison;h.context.renderClusterReport(r);
  assert.doesNotMatch(h.element('cluster-market').innerHTML,/cluster-pool-ratio-comparison|2.7027%/);
});

test('missing pair-denominated field never turns USD or native currency into a pool ratio',()=>{
  const h=harness(),r=unitRatioReportForUi();r.pool_vaults.market_comparison={status:'UNAVAILABLE',reason:'DIRECT_QUOTE_RATIO_UNAVAILABLE'};
  h.context.renderClusterReport(r);const html=h.element('cluster-market').innerHTML;
  assert.match(html,/直接币对报价字段缺失或无效/);assert.doesNotMatch(html,/2.7027%/);
});

function binaryHolderReportForUi() {
  const owner='11111111111111111111111111111112',account='11111111111111111111111111111113';
  return {...fixture,holder_rankings:{requested:true,status:'INCOMPLETE_EVIDENCE',snapshot_slot:100,response_sha256:'a'.repeat(64),owners:[],metrics:{},raw_balance_check:{version:1,status:'RECONCILED_NONZERO_BALANCE_MASS',mint,program_id:'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',full_positive_mass_reconciled:true,all_selected_accounts_decoded:true,independent_provider:false,roles_verified:false,enumeration_membership_independently_verified:false,enumeration_slot:100,snapshot_slot:101,enumeration_relation:'DIFFERENT_FINALIZED_SLOTS',enumeration_response_sha256:'a'.repeat(64),response_sha256:'b'.repeat(64),mint_supply_raw:'100',selected_total_raw:'100',decimals:0,selected_account_count:1,selected_accounts:[account],enumeration_account_count:1,accounts_not_selected:0,owner_top10_pct:'100.0000',records:[{token_account:account,mint,owner,raw:'100',status:'MATCH'}],owners:[{owner,raw:'100',observed_account_count:1,supply_pct:'100.0000'}]}}};
}

test('binary holder proof shows actual bank and unfiltered mass without independent-provider or role claim',()=>{
  const h=harness();h.context.renderClusterReport(binaryHolderReportForUi());const html=h.element('cluster-rankings').innerHTML;
  assert.match(html,/cluster-holder-binary/);assert.match(html,/同批非零余额已覆盖/);assert.match(html,/原始 Owner Top10/);
  assert.match(html,/100%/);assert.match(html,/100.*101/);assert.match(html,/同一 RPC/);assert.match(html,/独立提供方/);
});

test('partial, malformed and legacy binary proofs cannot retain a precise mass percentage',()=>{
  const h=harness(),r=binaryHolderReportForUi();h.context.renderClusterReport(r);
  r.holder_rankings.raw_balance_check.selected_total_raw='99';h.context.renderClusterReport(r);
  assert.doesNotMatch(h.element('cluster-rankings').innerHTML,/同批非零余额已覆盖|100%/);
  r.holder_rankings.raw_balance_check.status='OBSERVED_SAMPLE_ONLY';r.holder_rankings.raw_balance_check.reason='TOKEN_2022_MASS_SEMANTICS_UNVERIFIED';h.context.renderClusterReport(r);
  assert.match(h.element('cluster-rankings').innerHTML,/Token-2022/);assert.doesNotMatch(h.element('cluster-rankings').innerHTML,/100%/);
  delete r.holder_rankings.raw_balance_check;h.context.renderClusterReport(r);
  assert.doesNotMatch(h.element('cluster-rankings').innerHTML,/cluster-holder-binary|100%/);
});

test('equal binary balances use ASCII address order consistently with the backend',()=>{
  const h=harness(),r=binaryHolderReportForUi(),c=r.holder_rankings.raw_balance_check;
  const addresses=['11111111111111111111111111111113','11111111111111111111111111111114'],owners=['1111111111111111111111111111111Z','1111111111111111111111111111111a'];
  c.selected_accounts=addresses;c.selected_account_count=2;c.records=addresses.map((token_account,i)=>({token_account,mint,owner:owners[i],raw:'50',status:'MATCH'}));
  c.owners=owners.map(owner=>({owner,raw:'50',observed_account_count:1,supply_pct:'50.0000'}));
  h.context.renderClusterReport(r);assert.match(h.element('cluster-rankings').innerHTML,/同批非零余额已覆盖/);
});
