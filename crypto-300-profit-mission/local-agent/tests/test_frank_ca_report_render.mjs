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

function harness() {
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
  const store=new Map(),requests=[];
  const context={
    document:{
      getElementById:element,querySelectorAll:()=>[],
      addEventListener(){},body:{appendChild(){}},createElement:()=>element('__created'),
    },
    window:{location:{hash:'#cluster'},addEventListener(){}},
    history:{replaceState(){}},
    navigator:{clipboard:{writeText:async()=>{}}},
    localStorage:{getItem:k=>store.get('local:'+k)||null,setItem:(k,v)=>store.set('local:'+k,v)},
    sessionStorage:{getItem:k=>store.get('session:'+k)||null,setItem:(k,v)=>store.set('session:'+k,v),removeItem:k=>store.delete('session:'+k)},
    fetch:async(url,options={})=>{
      requests.push({url,method:options.method||'GET'});
      if(url==='/api/cluster-latest?mint='+encodeURIComponent(mint))
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
  vm.runInContext(source,context,{timeout:2500,filename:'app.js'});
  return {context,element,requests,store};
}

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
