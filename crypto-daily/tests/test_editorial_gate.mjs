import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { validateEditorial } from '../scripts/editorial_gate.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const rules=JSON.parse(fs.readFileSync(path.join(root,'EDITORIAL_RULESET.json'),'utf8'));
const headings=['一、今日最重要的5件事','二、BTC/ETH/SOL及主要资产','三、二级市场剧烈波动与持续趋势','四、监管与政策','五、机构、VC、基金、交易所、上市公司、做市商、鲸鱼真实资金动作','六、融资、协议、基础设施、稳定币、RWA、预测市场、AI/Crypto、DePIN及公链生态','七、空投、积分、TGE、ICO/公售、解锁和实际可参与机会','八、Early / Meme / NFT / 新生态热点','九、安全、黑客、漏洞、恶意App、脱锚、跑路、清算与重大解锁','十、全球局势与跨市场冲击','十一、未来24至72小时催化','十二、持续趋势与跨市场机会观察清单','十三、今日行动与风险结论'];
const mkEvent=(id,kind,impact='NICHE',rest={})=>({event_key:id,material_version:'v1',kind,source_url:'https://issuer.example/original',published_at:'2026-10-21T02:00:00Z',actual_delta:'A freshly verified event with a material new fact',impact,source_confirmed:true,status:'verified',...rest});
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
