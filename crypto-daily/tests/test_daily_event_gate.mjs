import test from 'node:test';
import assert from 'node:assert/strict';
import { validateReport } from '../scripts/daily_event_gate.mjs';

const headings = [
  '一、今日最重要的5件事', '二、BTC/ETH/SOL及主要资产', '三、二级市场剧烈波动与持续趋势',
  '四、监管与政策', '五、机构、VC、基金、交易所、上市公司、做市商、鲸鱼真实资金动作',
  '六、融资、协议、基础设施、稳定币、RWA、预测市场、AI/Crypto、DePIN及公链生态',
  '七、空投、积分、TGE、ICO/公售、解锁和实际可参与机会', '八、Early / Meme / NFT / 新生态热点',
  '九、安全、黑客、漏洞、恶意App、脱锚、跑路、清算与重大解锁',
  '十、全球局势与跨市场冲击', '十一、未来24至72小时催化',
  '十二、持续趋势与跨市场机会观察清单', '十三、今日行动与风险结论',
];
const lanes = ['labeled_btc', 'security', 'cex_policy', 'etf_flows', 'tge_rights', 'nft_social'];
const coverage = lanes.map(lane => ({lane, status:'checked', checked_at:'2026-10-21T02:00:00Z'}));
const body = (replacement = '') => headings.map((title,i) => title + '\n（1）' + (i===4?replacement:'当日核实的行业行情和实际变化。') + '\n（2）可量化的数据、期限和可执行观察依据。').join('\n\n');
const fresh = {event_key:'btc:clifton-collins:2026-10-20:tranche-5',family_key:'btc:clifton-collins',material_version:'tx:eb0bde50049e924590a1812af2d2699c13d513415d3f03bbe3d10f316b3d6756',aliases:['Clifton Collins'],asset:'BTC',amount_usd:41500000,source_tier:'primary-analytics',source_url:'https://info.arkm.com/research/clifton-collins-fifth-500-btc-40m-transfer-from-drug-dealers-lost-stack',published_at:'2026-10-20T17:25:00Z',material_delta:'Fifth distinct 500 BTC tranche went to Coinbase Prime after the prior August tranche.',decision:'include'};
const prior = {event_key:'btc:clifton-collins:2026-08-28:tranche-4',family_key:'btc:clifton-collins',material_version:'tx:prior',aliases:['Clifton Collins']};
const manifest = () => ({report_date:'2026-10-21',body:body('Clifton Collins第五批500 BTC转至Coinbase Prime，来源是Arkham。'),previous_events:[prior],candidates:[fresh],coverage});

test('fresh fifth transfer is distinct from fourth despite both being 500 BTC', () => assert.equal(validateReport(manifest()).passed,true));
test('must not miss material fresh Arkham transfer from final email', () => {
  const m=manifest();m.body=body();assert.ok(validateReport(m).errors.some(e=>e.startsWith('INCLUDED_CANDIDATE_MISSING')));
});
test('must not silently watch verified fresh >$10m labeled BTC flow', () => {
  const m=manifest();m.candidates=[{...fresh,decision:'watch',reason:'This is under verification despite primary analytics attribution.'}];
  assert.ok(validateReport(m).errors.some(e=>e.startsWith('MAJOR_BTC_TRANSFER_MUST_BE_INCLUDED')));
});
test('same event cannot repeat on following day without new material delta', () => {
  const m=manifest();m.previous_events=[prior,{...fresh}];
  assert.ok(validateReport(m).errors.some(e=>e.startsWith('REPEATED_WITHOUT_DELTA')));
});
test('old Qubic/Cysic/JPMD item without new delta is blocked', () => {
  const m=manifest();m.previous_events=[prior,{event_key:'qubic:wallet:2026-10-18',family_key:'qubic:wallet',material_version:'v1',aliases:['Qubic']}];
  m.body=body('Clifton Collins第5次500 BTC新转账，旧Qubic事件仍未改变。');
  assert.ok(validateReport(m).errors.some(e=>e.startsWith('HISTORICAL_NO_DELTA_REPEATED')));
});
test('same fresh story cannot occupy 8 lines across sections', () => {
  const m=manifest();m.body=m.body.replaceAll('当日核实的行业行情和实际变化。','Clifton Collins此次500 BTC转账，仍是同一笔交易。');
  assert.ok(validateReport(m).errors.some(e=>e.startsWith('EVENT_OVEREXPOSED')));
});
test('cannot omit labeled BTC discovery lane even if report has all sections', () => {
  const m=manifest();m.coverage=coverage.filter(c=>c.lane!=='labeled_btc');
  assert.ok(validateReport(m).errors.includes('MISSING_DISCOVERY_RECEIPT:labeled_btc'));
});
test('source_gap is warning not blanket daily email veto', () => {
  const m=manifest();m.coverage=coverage.map(c=>c.lane==='nft_social'?{...c,status:'source_gap'}:c);
  const r=validateReport(m);assert.equal(r.passed,true);assert.ok(r.warnings.includes('DISCOVERY_SOURCE_GAP:nft_social'));
});
test('per-section numbering must restart at 1', () => {
  const m=manifest();m.body=m.body.replace('二、BTC/ETH/SOL及主要资产\n（1）','二、BTC/ETH/SOL及主要资产\n（3）');
  assert.ok(validateReport(m).errors.some(e=>e.startsWith('SECTION_NUMBER_GAP')));
});

test('full 13-section report can have just 13 material items instead of filler', () => {
  const m=manifest();m.body=m.body.replace(/^（2）[^\n]*$/gm,'');
  const r=validateReport(m);assert.equal(r.passed,true);assert.equal(r.metrics.numbered_items,13);
});
