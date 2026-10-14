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
}
const report=structuredClone(results[0]);report.token_identity.display_label='身份来源冲突';report.token_identity.display_name=null;report.token_identity.conflict_status='TOKEN_IDENTITY_CONFLICT';report.token_identity.sources.push({name:'<script>wrong</script>',mint:report.mint});ctx.report=report;
vm.runInContext('renderClusterReport(report)',ctx);
assert(nodes['cluster-status'].innerHTML.includes('TOKEN_IDENTITY_CONFLICT'));
assert(nodes['cluster-summary'].innerHTML.includes('&lt;script&gt;wrong&lt;/script&gt;'));
assert(!nodes['cluster-summary'].innerHTML.includes('<script>wrong</script>'));
console.log('C02 actual app.js: 6 official cases, sequential mint isolation, preview, conflict and escaping PASS');
