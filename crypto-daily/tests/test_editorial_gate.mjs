import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { validateEditorial } from '../scripts/editorial_gate.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const rules=JSON.parse(fs.readFileSync(path.join(root,'EDITORIAL_RULESET.json'),'utf8'));
const headings=['一、今日最重要的5件事','二、BTC/ETH/SOL及主要资产','三、二级市场剧烈波动与持续趋势','四、监管与政策','五、机构、VC、基金、交易所、上市公司、做市商、鲸鱼真实资金动作','六、融资、协议、基础设施、稳定币、RWA、预测市场、AI/Crypto、DePIN及公链生态','七、空投、积分、TGE、ICO/公售、解锁和实际可参与机会','八、Early / Meme / NFT / 新生态热点','九、安全、黑客、漏洞、恶意App、脱锚、跑路、清算与重大解锁','十、全球局势与跨市场冲击','十一、未来24至72小时催化','十二、持续趋势与跨市场机会观察清单','十三、今日行动与风险结论'];
const mkEvent=(id,kind,impact='NICHE',rest={})=>({event_key:id,family_key:id,material_version:'v1',kind,source_url:'https://issuer.example/original',published_at:'2026-10-21T02:00:00Z',actual_delta:'A freshly verified event with a material new fact',impact,source_confirmed:true,status:'verified',...rest});
const base=()=>({
 market_core:['BTC','ETH','SOL'].map(symbol=>({symbol,price:82000,source_url:'https://api.binance.com/api/v3/ticker/24hr',observed_at:'2026-10-21T02:00:00Z'})),
 source_receipts:rules.full_report.minimum_domain_receipts.map(lane=>({lane,status:'checked',checked_at:'2026-10-21T02:00:00Z',query_or_url:'English original-source lookup',result_urls:['https://issuer.example/index']})),
 events:[mkEvent('fifth-500-btc','INSTITUTIONAL_FLOW','MAJOR',{priority:'HIGH'}),mkEvent('btc-tape','CORE_QUOTE'),mkEvent('balance-cca','TGE_PUBLIC_SALE','PERSONAL',{user_only:true}),mkEvent('systemic-security','MAJOR_SECURITY','SYSTEMIC',{impact_breadth:'multi-venue',top5_basis:'Fresh original security bulletin documents multi-venue exposure affecting a large set of custody accounts',top5_evidence_url:'https://issuer.example/incident'}),mkEvent('conclusion','ACTION_CONCLUSION')],
 previous_events:[],
 items:[
 {section:1,event_key:'systemic-security',role:'highlight',text:'大型安全事故波及多个机构钱包，官方正在确认处理。'},
 {section:2,event_key:'btc-tape',role:'detail',text:'BTC 82742美元、ETH 2447美元、SOL 106美元，包含来源时间与真实24小时成交量。'},
 {section:5,event_key:'fifth-500-btc',role:'detail',text:'Arkham发现Clifton Collins独立第五笔500 BTC转账，Coinbase Prime不是卖出证明。'},
 {section:7,event_key:'balance-cca',role:'detail',text:'BALANCE按其CCA公开拍卖规则评估当前报价、结算和未花预算退款。'},
 {section:9,event_key:'systemic-security',role:'detail',text:'官方事故公告包含受影响机构账户及跨场景安全补救步骤。'},
 {section:13,event_key:'conclusion',role:'detail',text:'结合新事实评估下一步资产风险及有效期限。'}
 ]});
function complete(x){
 x.items.sort((a,b)=>a.section-b.section);
 const counters={};x.empty_section_reasons=[];
 for(const it of x.items)it.item_number=counters[it.section]=(counters[it.section]||0)+1;
 x.body=headings.map((h,i)=>{
  const section=i+1, items=x.items.filter(t=>t.section===section);
  if(items.length)return h+'\n'+items.map(t=>'（'+t.item_number+'）'+t.text).join('\n');
  if(section!==1)x.empty_section_reasons.push({section,reason:'The original English materiality and source check did not produce independent new developments in this lane.',checked_lanes:['spot','onchain']});
  return h+'\n'+rules.full_report.empty_section_line;
 }).join('\n\n');
 return x;
}
function run(mutator=()=>{}){const x=base();mutator(x);complete(x);return validateEditorial(x,rules)}
test('13 headings and sourced concise full structure pass without padding',()=>assert.equal(run().passed,true));
test('balance bid cannot become a Top5 global item',()=>assert.ok(run(x=>{x.items[0].event_key='balance-cca'}).errors.some(e=>e.startsWith('TOP5_NOT_ELIGIBLE'))));
test('balance must be in TGE/public sale section 7, not fund-flows 5',()=>assert.ok(run(x=>{x.items.find(t=>t.event_key==='balance-cca').section=5}).errors.some(e=>e.startsWith('WRONG_PRIMARY_SECTION'))));
test('distinct fifth tranche is allowed as institutional flow in section 5',()=>assert.equal(run().passed,true));
test('must account for high-priority new labelled 500 BTC transfer',()=>assert.ok(run(x=>{x.items=x.items.filter(t=>t.event_key!=='fifth-500-btc')}).errors.some(e=>e.startsWith('UNACCOUNTED_HIGH_EVENT'))));
test('old version of same story is blocked',()=>assert.ok(run(x=>{x.previous_events=[{event_key:'balance-cca',material_version:'v1'}]}).errors.some(e=>e.startsWith('REPEATED_HISTORICAL_EVENT'))));
test('missing source discovery receipt is rejected',()=>assert.ok(run(x=>{x.source_receipts=x.source_receipts.filter(r=>r.lane!=='onchain')}).errors.some(e=>e.startsWith('DISCOVERY_LANE_RECEIPT_MISSING'))));
test('one inaccessible NFT source generates warning not total veto',()=>{const r=run(x=>{const c=x.source_receipts.find(c=>c.lane==='early_nft');c.status='source_gap';c.error='HTTP_403';c.result_urls=[];});assert.equal(r.passed,true);assert.ok(r.warnings.includes('SOURCE_GAP:early_nft'))});
test('missing real core market prices is failure even with 13 headings',()=>assert.ok(run(x=>{x.market_core=[]}).errors.some(e=>e.startsWith('MARKET_CORE_MISSING'))));
test('three numbered paragraphs about same event fail dedup',()=>assert.ok(run(x=>{x.items.push({section:5,event_key:'fifth-500-btc',role:'detail',text:'重复叙述同一笔500 BTC。'},{section:5,event_key:'fifth-500-btc',role:'detail',text:'第三遍重复叙述同一笔500 BTC。'})}).errors.some(e=>e.startsWith('OVEREXPOSED_EVENT'))));
test('item in wrong category section is caught',()=>assert.ok(run(x=>{x.items.find(t=>t.event_key==='balance-cca').section=8}).errors.some(e=>e.startsWith('WRONG_PRIMARY_SECTION'))));
test('cannot declare source checked with no actual source result',()=>assert.ok(run(x=>{x.source_receipts[0].result_urls=[]}).errors.some(e=>e.startsWith('CHECKED_WITHOUT_SOURCE_RESULT'))));

test('bare $41m wallet transfer not promoted to global Top5 merely by size',()=>assert.ok(run(x=>{x.items[0].event_key='fifth-500-btc';x.items.find(t=>t.event_key==='systemic-security'&&t.section===9).text='Wallet transfer is not a security loss';}).errors.some(e=>e.startsWith('TOP5_NOT_ELIGIBLE'))));
test('systemic top5 must have independent breadth evidence',()=>assert.ok(run(x=>{delete x.events.find(e=>e.event_key==='systemic-security').top5_evidence_url}).errors.some(e=>e.startsWith('TOP5_NOT_ELIGIBLE'))));

test('BALANCE overall Early project must use section 8, distinct from live CCA actions in 7',()=>{
 const r=run(x=>{
   x.events.push(mkEvent('balance-project','EARLY_NFT_MEME','NICHE',{user_only:true}));
   x.items.push({section:8,event_key:'balance-project',role:'detail',text:'BALANCE作为Jack Butcher早期艺术与代币项目的作品和估值机制。'});
 });
 assert.equal(r.passed,true);
});
test('BALANCE Early project in public-sale section without separate CCA event fails',()=>{
 const r=run(x=>{
   x.events.push(mkEvent('balance-project','EARLY_NFT_MEME','NICHE',{user_only:true}));
   x.items.push({section:7,event_key:'balance-project',role:'detail',text:'BALANCE艺术和代币项目基础介绍，不是新的CCA截止或退款操作。'});
 });
 assert.ok(r.errors.some(e=>e.startsWith('WRONG_PRIMARY_SECTION:balance-project')));
});

test('two independently checked ETF receipts are accepted within same coverage lane',()=>{
  const r=run(x=>{x.source_receipts.push({lane:'capital_flows',status:'checked',checked_at:'2026-10-22T02:00:00Z',query_or_url:'https://farside.co.uk/eth/',result_urls:['https://farside.co.uk/eth/']})});
  assert.equal(r.passed,true);
});
test('one verified security receipt plus one inaccessible specialist source is honest partial, not a hard fail',()=>{
  const r=run(x=>{x.source_receipts.push({lane:'security',status:'source_gap',checked_at:'2026-10-22T02:00:00Z',query_or_url:'English X specialist security source',error:'HTTP_403'})});
  assert.equal(r.passed,true);
  assert.ok(r.warnings.includes('SOURCE_GAP:security'));
});
test('malformed additional receipt is never waived by a good receipt in same lane',()=>{
  const r=run(x=>{x.source_receipts.push({lane:'capital_flows',status:'checked',checked_at:'2026-10-22T02:00:00Z',query_or_url:'https://farside.co.uk/eth/',result_urls:[]})});
  assert.ok(r.errors.some(x=>x.startsWith('CHECKED_WITHOUT_SOURCE_RESULT')));
});

test('critical web runtime RCE original-source lane cannot be omitted',()=>{
  const r=run(x=>{x.source_receipts=x.source_receipts.filter(c=>c.lane!=='web_runtime_rce')});
  assert.ok(r.errors.some(e=>e.startsWith('DISCOVERY_LANE_RECEIPT_MISSING:web_runtime_rce')));
});
test('global WebPKI/CA trust emergency original-source lane cannot be omitted',()=>{
  const r=run(x=>{x.source_receipts=x.source_receipts.filter(c=>c.lane!=='web_pki_tls')});
  assert.ok(r.errors.some(e=>e.startsWith('DISCOVERY_LANE_RECEIPT_MISSING:web_pki_tls')));
});
test('two independent real global security receipts can coexist with original crypto security checks',()=>{
 const r=run(x=>{x.source_receipts.push({lane:'web_runtime_rce',status:'checked',checked_at:'2026-10-22T03:30:00Z',query_or_url:'https://www.php.net/archive/2026.php',result_urls:['https://www.php.net/archive/2026.php']});
 x.source_receipts.push({lane:'web_pki_tls',status:'checked',checked_at:'2026-10-22T03:30:00Z',query_or_url:'https://blog.mozilla.org/security/',result_urls:['https://blog.mozilla.org/security/']});});
 assert.equal(r.passed,true);
});

test('AI package supply-chain original-source receipt is mandatory',()=>{
 const r=run(x=>{x.source_receipts=x.source_receipts.filter(y=>y.lane!=='ai_package_supply_chain')});
 assert.ok(r.errors.some(e=>e.startsWith('DISCOVERY_LANE_RECEIPT_MISSING:ai_package_supply_chain')));
});
test('cloud secret/OAuth original-source receipt is mandatory',()=>{
 const r=run(x=>{x.source_receipts=x.source_receipts.filter(y=>y.lane!=='cloud_secrets_identity')});
 assert.ok(r.errors.some(e=>e.startsWith('DISCOVERY_LANE_RECEIPT_MISSING:cloud_secrets_identity')));
});
test('Node Laravel framework authentication original-source receipt is mandatory',()=>{
 const r=run(x=>{x.source_receipts=x.source_receipts.filter(y=>y.lane!=='backend_framework_auth')});
 assert.ok(r.errors.some(e=>e.startsWith('DISCOVERY_LANE_RECEIPT_MISSING:backend_framework_auth')));
});
test('SaaS source-gap may warn but does not fabricate no-new-news or block other reliable content',()=>{
 const r=run(x=>{const y=x.source_receipts.find(t=>t.lane==='cloud_secrets_identity');y.status='source_gap';y.error='HTTP_403';y.result_urls=[];});
 assert.equal(r.passed,true);
 assert.ok(r.warnings.includes('SOURCE_GAP:cloud_secrets_identity'));
});

test('dated event key cannot bypass historical same-family version',()=>{
 const r=run(x=>{
   x.previous_events=[{event_key:'old-restore-Oct27',family_key:'systemic-security',material_version:'v1',delivered_date:'2026-10-27'}];
   x.events.find(e=>e.event_key==='systemic-security').event_key='new-restore-Oct28';
   x.events.find(e=>e.event_key==='new-restore-Oct28').family_key='systemic-security';
   x.items.filter(i=>i.event_key==='systemic-security').forEach(i=>i.event_key='new-restore-Oct28');
 });
 assert.ok(r.errors.some(e=>e.startsWith('REPEATED_FAMILY_VERSION:systemic-security')));
});
test('same incident reworded as a new dated key must prove concrete changed state',()=>{
 const r=run(x=>{
   x.previous_events=[{event_key:'security-yesterday',family_key:'systemic-security',material_version:'prior-restore-state'}];
   x.events.find(e=>e.event_key==='systemic-security').material_version='oct28-new-wording';
 });
 assert.ok(r.errors.some(e=>e.startsWith('FAMILY_REPLAY_WITHOUT_MATERIAL_STATE_CHANGE:systemic-security')));
});
test('genuine independently dated issuer restoration change passes family gate',()=>{
 const r=run(x=>{
   x.previous_events=[{event_key:'security-yesterday',family_key:'systemic-security',material_version:'restoration-pending'}];
   const ev=x.events.find(e=>e.event_key==='systemic-security');
   ev.material_version='restoration-live';
   ev.novelty_proof={previous_material_version:'restoration-pending',changed_field:'restore_state',old_value:'pending validation',new_value:'restoration is now live',evidence_url:'https://issuer.example/restoration-notice',evidence_published_at:'2026-10-28T08:01:00Z'};
   x.items.find(i=>i.event_key==='systemic-security'&&i.section===9).text+=' restoration is now live';
 });
 assert.equal(r.passed,true);
});
test('fake new state only in metadata but missing from email must not pass',()=>{
 const r=run(x=>{
   x.previous_events=[{event_key:'security-yesterday',family_key:'systemic-security',material_version:'pending'}];
   const e=x.events.find(e=>e.event_key==='systemic-security');e.material_version='new';
   e.novelty_proof={previous_material_version:'pending',changed_field:'restore_state',old_value:'pending',new_value:'fully restored',evidence_url:'https://issuer.example/real',evidence_published_at:'2026-10-28'};
 });
 assert.ok(r.errors.some(e=>e.startsWith('FAMILY_REPLAY_WITHOUT_MATERIAL_STATE_CHANGE')));
});
test('missing family key is hard error for narrative news',()=>{
 const r=run(x=>{delete x.events.find(e=>e.event_key==='systemic-security').family_key});
 assert.ok(r.errors.some(e=>e.startsWith('NEWS_EVENT_MISSING_FAMILY_KEY')));
});
