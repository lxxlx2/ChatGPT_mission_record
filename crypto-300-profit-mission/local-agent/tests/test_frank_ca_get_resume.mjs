import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { test } from 'node:test';
import vm from 'node:vm';

const root = new URL('../mission_agent/mission_control/static/', import.meta.url);
const app = readFileSync(new URL('app.js',root),'utf8');
const html = readFileSync(new URL('index.html',root),'utf8');
const styles = readFileSync(new URL('styles.css',root),'utf8');
const begin = app.indexOf('const CLUSTER_PENDING_KEY =');
const loaderStart = app.indexOf('async function loadLatestCluster(', begin);
const viewStart = app.indexOf('function setView(', loaderStart);
const recoveryStart = app.indexOf('function clusterShowRecovery(', viewStart);
const end = app.indexOf("$('cluster-form').addEventListener('submit'", recoveryStart);
const submitEnd = app.indexOf('\n// A browser reload', end);
assert.ok(begin >= 0 && loaderStart > begin && viewStart > loaderStart &&
  recoveryStart > viewStart && end > recoveryStart && submitEnd > end,
  'isolate real CA cache/recovery/submit functions, excluding unrelated live UI');
const loader = app.slice(loaderStart,viewStart);
const source = app.slice(begin,loaderStart) + app.slice(recoveryStart,end);
const submitSource = app.slice(end,submitEnd);
const mint = 'BXoHJdds8B2qnD4GkCQPMVFy97M3JmPo4TEk4kpump';
const id = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';

function makeHarness(results = [], saved = null, opts = {}) {
  const nodes = new Map(), listeners = {}, delays = [], calls = [], statuses = [], rendered = [];
  const storage = new Map();
  if (saved) storage.set('mission-meme-cluster-pending-v1', JSON.stringify(saved));
  let sequence = 0;
  const elements = (name) => {
    if (!nodes.has(name)) nodes.set(name, { hidden: true, disabled: false, value: '', textContent: '', addEventListener(_, fn) { listeners[name]=fn; } });
    return nodes.get(name);
  };
  const context = {
    $:elements,
    sessionStorage: {
      getItem:k=>storage.get(k)??null,
      setItem:(k,v)=>storage.set(k,v),
      removeItem:k=>storage.delete(k),
    },
    localStorage:{setItem(){}},
    get:async path=>{
      calls.push(path);
      const next=results.shift();
      if (next instanceof Error) throw next;
      if (next === undefined) throw new Error('unexpected GET');
      return await next;
    },
    clusterStatus:(...args)=>statuses.push(args),
    renderClusterPreview() {},
    renderClusterReport:(row)=>rendered.push(row),
    clusterProgressDetail:()=> '已查询信息',
    clusterErrorMessage:x=>String(x),
    loadLatestCluster:async()=>true,
    showToast() {},
    fetch:async (...args)=>{
      calls.push('POST:'+args[0]);
      if (opts.postFailure) throw new TypeError('Failed to fetch');
      throw new Error('Unexpected real POST');
    },
    setTimeout:(callback,ms)=>{
      const entry = { callback, ms, id:++sequence, cancelled:false };
      delays.push(entry);
      return entry;
    },
    clearTimeout:t=>{ if(t) t.cancelled=true; },
    console:{warn(){}}, Date, Math, Number, String, JSON,
  };
  vm.createContext(context);
  vm.runInContext(opts.realCache ? source.replace('function clusterShowRecovery(',loader+'\nfunction clusterShowRecovery(') : source,context);
  if (opts.submit) vm.runInContext(submitSource,context);
  return {context,nodes,elements,listeners,delays,calls,statuses,storage,rendered,
    async next() {
      const task=delays.find(x=>!x.cancelled&&!x.used);
      assert.ok(task,'expected scheduled GET retry');
      task.used=true;
      await task.callback();
      return task.ms;
    }};
}

test('the recovery UI controls exist and no hidden auto-repost is present',()=>{
  assert.match(html,/id="cluster-recovery"[^>]*hidden/);
  assert.match(html,/id="cluster-resume-get"/);
  assert.match(html,/id="cluster-read-cached"/);
  assert.match(styles,/\.cluster-recovery\[hidden\]\{display:none\}/);
  assert.doesNotMatch(source, /fetch\s*\(/);
  assert.doesNotMatch(source, /method\s*:\s*['"]POST/);
});

test('two transient connection failures retry only GET and retain the exact job',async()=>{
  const h=makeHarness([
    new TypeError('Failed to fetch'),
    new TypeError('Failed to fetch'),
    {job_id:id,mint,status:'RUNNING'},
    {job_id:id,mint,status:'DONE'},
  ]);
  h.context.clusterSetJob(id,mint);
  await h.context.pollClusterJob(id);
  assert.equal(h.elements('cluster-recovery').hidden,false);
  assert.equal(h.elements('cluster-submit').disabled,true);
  assert.equal(await h.next(),1500);
  assert.equal(await h.next(),3000);
  assert.equal(h.elements('cluster-recovery').hidden,true);
  assert.equal(await h.next(),1200);
  assert.equal(h.storage.has('mission-meme-cluster-pending-v1'),false);
  assert.match(h.statuses.at(-1).join(' '),/无法独立证明与本次分析一一对应/);
  assert.equal(h.elements('cluster-submit').disabled,false);
  assert.equal(h.calls.length,4);
  assert.ok(h.calls.every(path=>path==='/api/cluster-analysis?job_id='+id));
});

test('404 stops retries and offers historical reading without claiming same job',async()=>{
  const h=makeHarness([
    new Error('/api/cluster-analysis?job_id='+id+' 404'),
    {mint,observed_at:1792708806,coverage:{special_normalization_complete:false}},
  ]);
  h.context.clusterSetJob(id,mint);
  await h.context.pollClusterJob(id);
  assert.equal(h.delays.length,0);
  assert.equal(h.elements('cluster-recovery').hidden,false);
  assert.equal(h.elements('cluster-submit').disabled,false);
  await h.listeners['cluster-read-cached']();
  assert.equal(h.calls.length,2);
  assert.equal(h.calls[1],'/api/cluster-latest?mint='+encodeURIComponent(mint));
  assert.match(h.statuses.at(-1).join(' '),/与当前任务的关联未经核实/);
  assert.match(h.statuses.at(-1).join(' '),/覆盖仍不完整/);
});

test('manual resume reads the SAME ID and full backoff stops after three retries',async()=>{
  const h=makeHarness([
    new TypeError('Failed to fetch'),
    new TypeError('Failed to fetch'),
    new TypeError('Failed to fetch'),
    new TypeError('Failed to fetch'),
    {job_id:id,mint,status:'RUNNING'},
  ]);
  h.context.clusterSetJob(id,mint);
  await h.context.pollClusterJob(id);
  await h.next(); await h.next(); await h.next();
  assert.equal(h.delays.filter(t=>!t.cancelled&&!t.used).length,0);
  assert.equal(h.elements('cluster-submit').disabled,false);
  h.listeners['cluster-resume-get']();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.calls.length,5);
  assert.ok(h.calls.every(path=>path.includes('job_id='+id)));
});

test('a browser session restores only the recorded job using GET',async()=>{
  const h=makeHarness([{job_id:id,mint,status:'QUEUED'}],{id,mint});
  h.context.clusterRestorePending();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.calls.length,1);
  assert.equal(h.calls[0],'/api/cluster-analysis?job_id='+id);
  assert.equal(h.elements('cluster-mint').value,mint);
  assert.equal(h.delays.length,1);
});

test('a job identity mismatch never renders it as completed',async()=>{
  const h=makeHarness([{job_id:'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',mint,status:'DONE'}]);
  h.context.clusterSetJob(id,mint);
  await h.context.pollClusterJob(id);
  assert.equal(h.delays.length,0);
  assert.equal(h.elements('cluster-recovery').hidden,false);
  assert.match(h.statuses.at(-1).join(' '),/任务编号或代币与已提交任务不一致/);
});

function deferred() {
  let resolve, reject;
  const promise=new Promise((res,rej)=>{ resolve=res; reject=rej; });
  return {promise,resolve,reject};
}
const mintB='So11111111111111111111111111111111111111112';
const idB='bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';

test('P2-1: late historical cache A cannot change active B, report or status',async()=>{
  const a=deferred();
  const h=makeHarness([a.promise],null,{realCache:true});
  h.elements('cluster-mint').value=mint;
  h.context.clusterSetJob(id,mint);
  const loading=h.listeners['cluster-read-cached']();
  h.context.clusterSetJob(idB,mintB);
  h.elements('cluster-mint').value=mintB;
  a.resolve({mint,observed_at:1792708806,coverage:{special_normalization_complete:false}});
  await loading;
  assert.equal(h.rendered.length,0);
  assert.equal(h.elements('cluster-mint').value,mintB);
  assert.equal(h.statuses.length,0);
  assert.equal(h.elements('cluster-recovery').hidden,true);
});

test('P2-1: late auto-loaded prior cache A cannot overwrite restored job B',async()=>{
  const a=deferred();
  const h=makeHarness([a.promise,{job_id:idB,mint:mintB,status:'RUNNING'}],
    {id:idB,mint:mintB},{realCache:true});
  h.elements('cluster-mint').value='';
  const old=h.context.loadLatestCluster(mint,true);
  h.context.clusterRestorePending();
  await new Promise(resolve=>setImmediate(resolve));
  a.resolve({mint,observed_at:1792708806});
  await old;
  assert.equal(h.elements('cluster-mint').value,mintB);
  assert.equal(h.rendered.length,0);
  assert.equal(h.calls[1],'/api/cluster-analysis?job_id='+idB);
  assert.equal(h.storage.has('mission-meme-cluster-pending-v1'),true);
});

test('P2-1: stale DONE report from job A cannot overwrite newly active B',async()=>{
  const a=deferred();
  const h=makeHarness([{job_id:id,mint,status:'DONE'},a.promise],null,{realCache:true});
  h.elements('cluster-mint').value=mint;
  h.context.clusterSetJob(id,mint);
  const completion=h.context.pollClusterJob(id);
  await new Promise(resolve=>setImmediate(resolve));
  h.context.clusterSetJob(idB,mintB);
  h.elements('cluster-mint').value=mintB;
  a.resolve({mint,observed_at:1792708806});
  await completion;
  assert.equal(h.rendered.length,0);
  assert.equal(h.elements('cluster-mint').value,mintB);
  assert.equal(h.storage.get('mission-meme-cluster-pending-v1').includes(idB),true);
});

test('P2-2: DONE report GET fails and manual recovery retries only report GET',async()=>{
  const h=makeHarness([
    {job_id:id,mint,status:'DONE'},
    new TypeError('Failed to fetch'),
    {mint,observed_at:1792708806,coverage:{special_normalization_complete:false}},
  ],null,{realCache:true});
  h.elements('cluster-mint').value=mint;
  h.context.clusterSetJob(id,mint);
  await h.context.pollClusterJob(id);
  assert.equal(h.elements('cluster-recovery').hidden,false);
  assert.equal(h.elements('cluster-submit').disabled,true);
  assert.equal(h.elements('cluster-resume-get').textContent,'重试读取报告');
  assert.ok(h.storage.get('mission-meme-cluster-pending-v1').includes(id));
  h.listeners['cluster-resume-get']();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.calls.length,3);
  assert.equal(h.calls[1],'/api/cluster-latest?mint='+mint);
  assert.equal(h.calls[2],'/api/cluster-latest?mint='+mint);
  assert.equal(h.elements('cluster-submit').disabled,false);
  assert.equal(h.storage.has('mission-meme-cluster-pending-v1'),false);
  assert.equal(h.rendered.length,1);
});

test('P2-3: failed new POST B cannot resurrect previous pending job A after refresh',async()=>{
  const h=makeHarness([],null,{submit:true,postFailure:true});
  h.context.clusterSetJob(id,mint);
  h.elements('cluster-mint').value=mintB;
  h.elements('cluster-preset').value='deep';
  await h.listeners['cluster-form']({preventDefault(){}});
  assert.equal(h.storage.has('mission-meme-cluster-pending-v1'),false);
  assert.match(h.statuses.at(-1).join(' '),/提交状态未核实/);
  assert.equal(h.elements('cluster-recovery').hidden,false);
  assert.equal(h.elements('cluster-resume-get').hidden,true);
  assert.equal(h.elements('cluster-mint').value,mintB);
  h.context.clusterRestorePending();
  assert.equal(h.calls.length,1);
  assert.equal(h.calls[0],'POST:/api/cluster-analysis');
  assert.equal(h.rendered.length,0);
});


test('DONE job renders same-ID persisted report with verified identity, not blanket completeness',async()=>{
  const h=makeHarness([
    {job_id:id,mint,status:'DONE'},
    {mint,ca_job_id:id,observed_at:1792708806,coverage:{special_normalization_complete:false}},
  ],null,{realCache:true});
  h.elements('cluster-mint').value=mint;
  h.context.clusterSetJob(id,mint);
  await h.context.pollClusterJob(id);
  assert.equal(h.rendered.length,1);
  assert.equal(h.rendered[0].ca_job_id,id);
  assert.equal(h.storage.has('mission-meme-cluster-pending-v1'),false);
  assert.match(h.statuses.at(-1).join(' '),/任务编号与已结束任务一致/);
  assert.match(h.statuses.at(-1).join(' '),/完整性仍须另行核实/);
  assert.ok(h.calls.every(path=>!path.startsWith('POST:')));
});

test('DONE job MUST NOT display a newer different-job same-Mint latest report',async()=>{
  const h=makeHarness([
    {job_id:id,mint,status:'DONE'},
    {mint,ca_job_id:idB,observed_at:1792708806,coverage:{}},
  ],null,{realCache:true});
  h.elements('cluster-mint').value=mint;
  h.context.clusterSetJob(id,mint);
  await h.context.pollClusterJob(id);
  assert.equal(h.rendered.length,0);
  assert.equal(h.elements('cluster-recovery').hidden,false);
  assert.equal(h.elements('cluster-submit').disabled,true);
  assert.ok(h.storage.get('mission-meme-cluster-pending-v1').includes(id));
  assert.equal(h.context.clusterReportLoadError,'IDENTITY');
  assert.equal(h.calls.length,2);
  assert.equal(h.calls.filter(p=>p.startsWith('POST:')).length,0);
});

test('legacy report without ca_job_id remains explicit unverified historical reading',async()=>{
  const h=makeHarness([
    {job_id:id,mint,status:'DONE'},
    {mint,observed_at:1792708806,coverage:{special_normalization_complete:false}},
  ],null,{realCache:true});
  h.elements('cluster-mint').value=mint;
  h.context.clusterSetJob(id,mint);
  await h.context.pollClusterJob(id);
  assert.equal(h.rendered.length,1);
  assert.match(h.statuses.at(-1).join(' '),/缺少可核对的本次任务编号/);
  assert.doesNotMatch(h.statuses.at(-1).join(' '),/任务编号与已结束任务一致/);
});
