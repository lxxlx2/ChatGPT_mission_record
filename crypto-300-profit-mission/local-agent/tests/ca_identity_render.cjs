// Executes the real app.js renderer against official saved identity results.
const fs=require('node:fs');const vm=require('node:vm');const assert=require('node:assert/strict');const path=require('node:path');
const root=path.resolve(__dirname,'..');const nodes={};
const node=id=>nodes[id] ||= {innerHTML:'',textContent:'',hidden:false,value:'',addEventListener(){},classList:{toggle(){},add(){},remove(){}},querySelectorAll(){return []}};
const ctx={console,document:{getElementById:node,querySelectorAll(){return []},addEventListener(){}},window:{location:{hash:'#cluster'},addEventListener(){}},history:{replaceState(){}},localStorage:{getItem(){return null},setItem(){}},setInterval(){},setTimeout(){},clearTimeout(){},fetch:async()=>({ok:true,json:async()=>({})})};
vm.createContext(ctx);
let source=fs.readFileSync(path.join(root,'mission_agent/mission_control/static/app.js'),'utf8').replace('\nrefresh();','\n');
vm.runInContext(source,ctx);
const results=JSON.parse(fs.readFileSync(path.resolve(root,'../meme/evidence/c02/real-case-results.json')));
for(const report of results){
  ctx.report=report;vm.runInContext('renderClusterReport(report)',ctx);
  assert(nodes['cluster-summary'].innerHTML.includes(report.mint));
  assert(nodes['cluster-summary'].innerHTML.includes(report.token_identity.display_label));
  assert(!nodes['cluster-summary'].innerHTML.includes('Agency</span><span class="subvalue">Agency'));
  ctx.job={preview:{token_status:report.token_profile.status,token_identity:report.token_identity,market_status:report.market.status},status:'RUNNING'};
  vm.runInContext('renderClusterPreview(job)',ctx);
  assert(nodes['cluster-preview'].innerHTML.includes(report.token_identity.display_label));
  assert(nodes['cluster-preview'].innerHTML.includes(report.mint));
  // Scan progress must differentiate same-name mints before final report.
  ctx.job={mint:report.mint,progress:{stage:'BASE_READY',token_identity:report.token_identity},status:'RUNNING'};
  const progress=vm.runInContext('clusterProgressDetail(job)',ctx);
  assert(progress.includes(report.mint.slice(0,6)));
  assert(progress.includes(report.mint.slice(-6)));
}
const report=structuredClone(results[0]);report.token_identity.display_label='身份来源冲突';report.token_identity.display_name=null;report.token_identity.conflict_status='TOKEN_IDENTITY_CONFLICT';report.token_identity.sources.push({name:'<script>wrong</script>',mint:report.mint});ctx.report=report;
vm.runInContext('renderClusterReport(report)',ctx);
assert(nodes['cluster-status'].innerHTML.includes('TOKEN_IDENTITY_CONFLICT'));
assert(nodes['cluster-identity-evidence'].innerHTML.includes('&lt;script&gt;wrong&lt;/script&gt;'));
assert(!nodes['cluster-identity-evidence'].innerHTML.includes('<script>wrong</script>'));
assert(!nodes['cluster-summary'].innerHTML.includes('metadata_attempts'), 'raw source data must not occupy the top summary grid');
assert(nodes['cluster-identity-evidence'].innerHTML.includes('<details>'), 'source trail must be opt-in detail');
console.log('C02 actual app.js: 6 official cases, exact CA preview/progress, conflict and escaping PASS');

const stale={mint:results[0].mint, token_identity:{display_label:'SYNTHETIC SAME-NAME TOKEN',
  identity_status:'UNCONFIRMED',market_match_status:'NOT_CHECKED',conflict_status:'UNRESOLVED',
  sources:[{source:'SYNTHETIC_ONLY',mint:results[0].mint}]},
  token_profile:{status:'UNAVAILABLE'},market:{status:'UNAVAILABLE'},
  assessment:{chain_permission_status:'UNRESOLVED',cluster_status:'WALLET_CLUSTER_UNRESOLVED',
    trading_status:'UNRESOLVED'},coverage:{rpc_calls:0}};
ctx.report=stale;
vm.runInContext('renderClusterReport(report)',ctx);
const badEvidence=nodes['cluster-token-profile'].innerHTML;
assert(badEvidence.includes('活动扩展风险'));
assert(badEvidence.includes('未确认'));
assert(!badEvidence.includes('已核实未发现'));
assert(!badEvidence.includes('class="ok-text">未发现'), 'unknown extension state cannot be green');
assert(!badEvidence.includes('class="ok-text">无'), 'unknown must not be marked clean');
assert(nodes['cluster-coverage'].innerHTML.includes('使用 RPC 节点</span><strong>0</strong>'));
assert(!nodes['cluster-coverage'].innerHTML.includes('使用 RPC 节点</span><strong>1</strong>'));
const clean=structuredClone(stale);
clean.token_profile={status:'OK',extensions:[],active_extension_risks:[],
  inactive_sensitive_extensions:[],unresolved_sensitive_extensions:[]};
clean.assessment.chain_permission_status='PASS';
ctx.report=clean;
vm.runInContext('renderClusterReport(report)',ctx);
assert(nodes['cluster-token-profile'].innerHTML.includes('已核实未发现'));
console.log('C02 Safari regression: unknown risk never green, zero RPC stays zero, audit details moved PASS');
