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
const end = app.indexOf("$('cluster-form').addEventListener('submit'", begin);
assert.ok(begin >= 0 && end > begin, 'load only the standalone CA recovery implementation');
const source = app.slice(begin, end);
const mint = 'BXoHJdds8B2qnD4GkCQPMVFy97M3JmPo4TEk4kpump';
const id = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';

function makeHarness(results = [], saved = null) {
  const nodes = new Map(), listeners = {}, delays = [], calls = [], statuses = [];
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
      return next;
    },
    clusterStatus:(...args)=>statuses.push(args),
    renderClusterPreview() {},
    renderClusterReport() {},
    clusterProgressDetail:()=> '已查询信息',
    clusterErrorMessage:x=>String(x),
    loadLatestCluster:async()=>true,
    setTimeout:(callback,ms)=>{
      const entry = { callback, ms, id:++sequence, cancelled:false };
      delays.push(entry);
      return entry;
    },
    clearTimeout:t=>{ if(t) t.cancelled=true; },
    console:{warn(){}}, Date, Math, Number, String, JSON,
  };
  vm.createContext(context);
  vm.runInContext(source,context);
  return {context,nodes,elements,listeners,delays,calls,statuses,storage,
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
