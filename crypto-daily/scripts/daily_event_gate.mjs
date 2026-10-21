import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HEADINGS = [
  '一、今日最重要的5件事',
  '二、BTC/ETH/SOL及主要资产',
  '三、二级市场剧烈波动与持续趋势',
  '四、监管与政策',
  '五、机构、VC、基金、交易所、上市公司、做市商、鲸鱼真实资金动作',
  '六、融资、协议、基础设施、稳定币、RWA、预测市场、AI/Crypto、DePIN及公链生态',
  '七、空投、积分、TGE、ICO/公售、解锁和实际可参与机会',
  '八、Early / Meme / NFT / 新生态热点',
  '九、安全、黑客、漏洞、恶意App、脱锚、跑路、清算与重大解锁',
  '十、全球局势与跨市场冲击',
  '十一、未来24至72小时催化',
  '十二、持续趋势与跨市场机会观察清单',
  '十三、今日行动与风险结论',
];
const LANES = ['labeled_btc', 'security', 'cex_policy', 'etf_flows', 'tge_rights', 'nft_social'];
const normalized = value => String(value ?? '').toLowerCase().normalize('NFKC');
const counted = (lines, aliases) => lines.filter(line => aliases.some(alias => normalized(line).includes(normalized(alias)))).length;

export function validateReport(input) {
  const errors = [];
  const warnings = [];
  const body = String(input.body ?? '');
  const lines = body.split(/\r?\n/);
  const items = [];
  const headings = [];
  let section = -1;
  let sectionIndex = 0;
  for (const line of lines) {
    if (/^[一二三四五六七八九十]+、/.test(line)) {
      headings.push(line.trim());
      section += 1;
      sectionIndex = 0;
      continue;
    }
    const match = /^（(\d+)）(.+)$/.exec(line);
    if (match) {
      sectionIndex += 1;
      if (Number(match[1]) !== sectionIndex) errors.push('SECTION_NUMBER_GAP:' + (section + 1) + ':' + match[1]);
      items.push(match[2]);
    }
  }
  if (headings.length !== HEADINGS.length || headings.some((h, i) => h !== HEADINGS[i])) errors.push('CANONICAL_13_HEADINGS_MISMATCH');
  if (items.length === 0) errors.push('REPORT_HAS_NO_SUBSTANTIVE_ITEMS');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(input.report_date ?? ''))) errors.push('INVALID_REPORT_DATE');

  const coverage = Array.isArray(input.coverage) ? input.coverage : [];
  for (const lane of LANES) {
    const receipts = coverage.filter(c => c.lane === lane);
    if (receipts.length !== 1 || !['checked', 'source_gap'].includes(receipts[0]?.status) || !receipts[0]?.checked_at) {
      errors.push('MISSING_DISCOVERY_RECEIPT:' + lane);
    } else if (receipts[0].status === 'source_gap') {
      warnings.push('DISCOVERY_SOURCE_GAP:' + lane);
    }
  }

  const candidates = Array.isArray(input.candidates) ? input.candidates : [];
  const history = Array.isArray(input.previous_events) ? input.previous_events : [];
  const newFamilyVersions = new Set();
  const keys = new Set();
  for (const candidate of candidates) {
    const { event_key, family_key, material_version, aliases, decision } = candidate;
    if (!event_key || !family_key || !material_version || !Array.isArray(aliases) || aliases.length === 0) {
      errors.push('INVALID_CANDIDATE_ID');
      continue;
    }
    if (keys.has(event_key)) errors.push('DUPLICATE_CANDIDATE:' + event_key);
    keys.add(event_key);
    if (!['include', 'watch', 'exclude'].includes(decision)) errors.push('UNACCOUNTED_CANDIDATE:' + event_key);
    if (!/^https:\/\//.test(candidate.source_url ?? '') || !candidate.published_at) errors.push('MISSING_SOURCE_PROVENANCE:' + event_key);
    const prior = history.find(h => h.event_key === event_key || (h.family_key === family_key && h.material_version === material_version));
    const hasDelta = !prior && String(candidate.material_delta ?? '').trim().length >= 15;
    if (hasDelta && decision === 'include') newFamilyVersions.add(family_key);
    if (decision === 'include') {
      if (!hasDelta) errors.push('REPEATED_WITHOUT_DELTA:' + event_key);
      const appearances = counted(items, aliases);
      if (appearances === 0) errors.push('INCLUDED_CANDIDATE_MISSING_FROM_BODY:' + event_key);
      if (appearances > 2) errors.push('EVENT_OVEREXPOSED:' + event_key + ':' + appearances);
    }
    if (decision !== 'include' && counted(items, aliases) > 0 && !hasDelta) errors.push('OLD_EVENT_IN_BODY:' + event_key);
    if (decision !== 'include' && String(candidate.reason ?? '').trim().length < 25) errors.push('MISSING_EXCLUSION_REASON:' + event_key);
    if (Number(candidate.amount_usd) >= 10000000 && candidate.asset === 'BTC' && candidate.source_tier === 'primary-analytics' && hasDelta && decision !== 'include') {
      errors.push('MAJOR_BTC_TRANSFER_MUST_BE_INCLUDED:' + event_key);
    }
  }
  for (const previous of history) {
    if (!Array.isArray(previous.aliases) || previous.aliases.length === 0) continue;
    if (newFamilyVersions.has(previous.family_key)) continue;
    const appearances = counted(items, previous.aliases);
    if (appearances > 0) errors.push('HISTORICAL_NO_DELTA_REPEATED:' + previous.event_key + ':' + appearances);
  }
  return {
    passed: errors.length === 0,
    errors: [...new Set(errors)],
    warnings,
    metrics: { headings: headings.length, numbered_items: items.length, candidates: candidates.length, discovery_lanes: coverage.length },
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.length !== 3) {
    process.stderr.write('Usage: node crypto-daily/scripts/daily_event_gate.mjs manifest.json\n');
    process.exitCode = 2;
  } else {
    const manifest = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
    const result = validateReport(manifest);
    process.stdout.write(JSON.stringify(result, null, 2) + '\n');
    if (!result.passed) process.exitCode = 1;
  }
}
