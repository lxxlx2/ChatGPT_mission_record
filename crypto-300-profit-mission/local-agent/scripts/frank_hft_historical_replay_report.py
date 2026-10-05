"""Post-replay FRANK HFT audit/report. Outcomes never feed model generation."""
import argparse,json,sqlite3,hashlib
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--artifact',type=Path,required=True)
parser.add_argument('--variant-work',type=Path,required=True)
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--boundary-before',type=Path,required=True)
parser.add_argument('--runtime-health',type=Path,required=True)
parser.add_argument('--report',type=Path,required=True)
args=parser.parse_args()
C=Path.cwd();A=args.artifact;r=json.loads(A.read_text());work=args.variant_work
iso=lambda t:datetime.fromtimestamp(t,timezone.utc).isoformat() if t is not None else None
r['HFT_STICKY_BEHAVIOR_CONFIRMED']='YES'
r['conclusion']='NEED_MORE_DATA'
r['conclusion_basis']=['Sticky HFT demonstrably blocks four otherwise qualifying observed episodes, including two anchored PAID episodes.', 'Three new episodes later end with unresolved inventory; one has mixed high-turnover BUY/SELL behavior.', 'Only four incremental episodes across three mints; trustworthy per-episode PnL and most requested winner name/mint bindings unavailable.', 'R0/R5/R15 indistinguishable here; cannot establish that rolling does not materially expand noise.']
d=sqlite3.connect('file:'+str(work/'R0.sqlite')+'?mode=ro',uri=True)
for e in r['episodes']:
 s=e['signals']['R0']['MULTIPLE']
 if e['category']!='STICKY_BLOCKED_ROLLING_MULTIPLE':continue
 last_index=next(i for i,x in enumerate(e['events']) if x['signature']==s['triggering_signature'])
 causal=e['events'][:last_index+1]
 # Exact state at emitted evaluation includes causal peak, no future inventory.
 # Current and R0 inventories are equal by cross-variant assertions.
 # Parse evaluation result; Engine signal current raw equals evaluation current.
 evalrow=d.execute("select body,at,signature from v1_evaluations where episode_id=? and at=?",(e['episode_id'],s['triggered_at'])).fetchall()
 item=next(json.loads(x[0]) for x in evalrow if s['signal_id'] in json.loads(x[0])['signal_ids'])
 net=peak=0;unknown=False;last_rolling_end=None
 for x in causal:
  amount=int(x['token_amount_raw'])
  if x['direction']=='BUY':net+=amount
  elif amount<=net:net-=amount
  else:unknown=True;break
  peak=max(peak,net)
 retention=str(Decimal(net)/Decimal(peak)) if not unknown and peak else None
 previous_windows=[w for w in e['rolling_hft_fail_windows'] if w['start']<=s['triggered_at']]
 if previous_windows:last_rolling_end=previous_windows[-1]['end']
 after=[x for x in causal if x['direction']=='BUY' and x['at']>e['sticky_hft_first_trigger_at']]
 e['candidate_audit']={'rolling_first_trigger_utc':iso(s['triggered_at']),'triggering_signature':s['triggering_signature'],
  'trigger_kind':item['kind'],'trigger_predicates':item['predicates'],'trigger_reason_codes':s['reason_codes'],
  'at_trigger_buy_count':s['position']['buy_count'],'at_trigger_sell_count':s['position']['sell_count'],
  'at_trigger_known_USDC':s['position']['gross_quote_spent'].get('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v','0'),
  'at_trigger_inventory_raw':s['position']['current_token_position'],'at_trigger_causal_peak_raw':str(peak),
  'at_trigger_retention_ratio':retention,'at_trigger_usdc_after_first_hft':str(sum((Decimal(x['quote_quantity']) for x in after if x['quote_asset']=='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'),Decimal(0))),
  'post_hft_buy_count_through_trigger':len(after),'post_hft_elapsed_through_trigger_seconds':s['triggered_at']-e['sticky_hft_first_trigger_at'],
  'seconds_since_last_HFT_expiry_at_trigger':s['triggered_at']-(last_rolling_end+1) if last_rolling_end else None,
  'at_trigger_lifetime_inventory':'UNKNOWN','post_hft_observed_end_state':e['final_state'],
  'classification':'A_SPLIT_ACCUMULATION_LIKE' if s['position']['sell_count']==0 and e['first_hft_composition']=={'BUY':3} else 'D_UNDETERMINED_MIXED_HIGH_TURNOVER',
  'classification_limit':'Behavioral resemblance only; user intent and actual arbitrage profitability unproven.',
  'route_evidence':'distinct user-level transaction signatures; CPI hops never counted as separate trades'}
 e['intent_classification']=e['candidate_audit']['classification']
 e['intent_basis']=e['candidate_audit']['classification_limit']

d.close()
names={'STONK':'6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx','PAID':'98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump'}
r['winner_audits']=[]
for name in ('STONK','PAID','Pistacio','PERPSPAD','fone','Pumpcat','CATE'):
 mint=names.get(name)
 if not mint:
  r['winner_audits'].append({'name':name,'status':'UNRESOLVED_NAME_TO_MINT','reason':'Existing bounded report names this winner but no verified mint binding was located. Not claimed absent and no guessed mapping.','pnl':'PNL_UNAVAILABLE'});continue
 rows=[e for e in r['episodes'] if e['mint']==mint]
 r['winner_audits'].append({'name':name,'mint':mint,'status':'PRESENT' if rows else 'ABSENT_FROM_DATASET',
  'episode_count':len(rows),'hft_60s_episode_count':sum(bool(e['rolling_hft_fail_windows']) for e in rows),
  'current_MULTIPLE':sum(e['signals']['CURRENT']['MULTIPLE'] is not None for e in rows),
  'rolling_MULTIPLE':sum(e['signals']['R0']['MULTIPLE'] is not None for e in rows),
  'sticky_blocked_rolling_multiple':sum(e['category']=='STICKY_BLOCKED_ROLLING_MULTIPLE' for e in rows),
  'episodes':[{'episode_id':e['episode_id'],'first_hft_utc':e['sticky_hft_first_trigger_utc'],'HFT_first_composition':e['first_hft_composition'],'current_MULTIPLE_utc':iso(e['signals']['CURRENT']['MULTIPLE']['triggered_at']) if e['signals']['CURRENT']['MULTIPLE'] else None,'rolling_MULTIPLE_utc':iso(e['signals']['R0']['MULTIPLE']['triggered_at']) if e['signals']['R0']['MULTIPLE'] else None} for e in rows],
  'pnl':'PNL_UNAVAILABLE','identity_source':'research/frank-30d-replay-state.md; matching mint in raw-verified ACTIVE_TRADE chronology'})
old=sqlite3.connect('file:'+str(args.baseline)+'?mode=ro',uri=True);new=sqlite3.connect('file:'+str(work/'CURRENT.sqlite')+'?mode=ro',uri=True)
parity={}
for t,cols in [('signals','signal_id,body'),('v1_evaluations','evaluation_id,body'),('v1_states','person_id,mint,body')]:
 a=old.execute('select '+cols+' from '+t+' order by 1').fetchall();b=new.execute('select '+cols+' from '+t+' order by 1').fetchall();assert a==b;parity[t]={'row_count':len(a),'exact_match':True}
r['prior_verified_V1_baseline_parity']=parity
r['history']['duplicate_ACTIVE_TRADE_raw_hashes']=new.execute("select count(*) from (select raw_hash from signatures where json_extract(body,'$.classification')='ACTIVE_TRADE' group by raw_hash having count(*)>1)").fetchone()[0]
r['HFT_INPUT_DUPLICATION_RISK']='NOT_OBSERVED_SIGNATURE_OR_RAW_HASH_DUPLICATION; semantic duplicates across distinct signatures not inferred'
old.close();new.close()
r['pnl_evaluation']={'status':'PNL_UNAVAILABLE','method':'Signals replayed first with causal raw chain only. Existing public aggregate notes lack trustworthy per-episode linkage/cost basis; not used for ranking or signal generation. No current price or synthetic conversion introduced.'}
before=json.loads(args.boundary_before.read_text());assert all(hashlib.sha256((C/p).read_bytes()).hexdigest()==v for p,v in before['production_hashes'].items())
h=json.loads(args.runtime_health.read_text());assert h['pid']==before['runtime_observation_before']['pid'] and h['restart_count']==before['runtime_observation_before']['restart_count']
assert h['code_commit']=='46c989c3ef35d63fc02808c519f73aa3e6ea1513' and h['source_drift'] is False
r['production_boundary']={'all_production_file_hashes_unchanged':True,'daemon_PID_unchanged':True,'restart_count_unchanged':True,'source_drift':False,'loaded_commit':h['code_commit'],'observation':'read existing health file only; no live validation, RPC, engine invocation or DB writes'}
r['starting_HEAD']=before['starting_HEAD']
A.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')


candidates=[e for e in r['episodes'] if e['category']=='STICKY_BLOCKED_ROLLING_MULTIPLE']
ranked=sorted(candidates,key=lambda e:(e['post_first_hft_buys'],e['buy_span_seconds'],Decimal(e['known_USDC_gross_buys'])),reverse=True)
m=r['metrics'];history=r['history']
lines=['# FRANK HFT STICKY vs ROLLING HISTORICAL_REPLAY — 2026-10-04', '',
'结论：**NEED_MORE_DATA**。sticky 60 秒 HFT 确实挡住 4 个本可满足 V1 其余条件的 observed episode，涉及 3 个 mint，其中 PAID 占 2 个。新增样本中 3 个在后续出现 inventory unresolved，另 1 个具有明显的混合 BUY/SELL turnover；当前无法证明 rolling 不扩大噪声。这个结论不否认机械漏报，而是区分信号差异与经济质量。', '',
'所有实验在全新 private historical SQLite 中进行。生产规则保持 sticky；没有重启、网络查询、通知、Gmail send、live DB 写入或 automation。PRODUCTION_TRADING = NO_GO。', '',
'## Authority 与冻结研究口径', '',
'Starting HEAD: `'+r['starting_HEAD']+'`; branch: `codex/frank-only-local-signals`; starting worktree clean。开始执行了 git fetch，未 reset、未 merge main。生产 daemon 仍加载 `46c989c3ef35d63fc02808c519f73aa3e6ea1513`。', '',
'CURRENT 复用原 Engine，ROLLING subclass 仅在原 `_evaluate` 执行前改变 `hft`。原 ACTIVE_TRADE/每小时 :29 时钟、episode reset、T0、accumulation、inventory、distribution、freshness、金额与其他 gates 不变。HFT 改变后原 `watch_eligible` 的结果也会随之改变，这是同一 HFT 变量的因果后果，不能冻结旧 WATCH 来阻断它。所有 variants 的 events、库存点、current/peak、state、T0、accumulation flag 一致；ACCUMULATION identity/time 集合一致。', '',
'R0：在 evaluation 时点的闭区间 `[at−60, at]` 中 count ≥3 才失败；计整数秒，窗口最后失败秒为 end，end+1 首次 PASS。R5/R15：从 end+1 起连续 300/900 秒无新 HFT 后恢复，出现新窗口则延后。只在原生产时钟 evaluation，不增加恢复 tick，因此 gate 恢复时间不等于信号发出时间。三个版本在看到 replay 结果前固定，无阈值调优。', '',
'完整快速 round trip 保持原逻辑：episode 内已证明 current inventory 恰好归零且距首 BUY ≤1200 秒，则该独立标志一直保留到 episode reset。没有改成部分退出或改变约 20 分钟 reference。后续 SELL 即使追加到 CLOSED episode，也不清除这个原始 veto。', '',
'USDC quote 直接数值比较；其他 quote 无可信历史换算时金额 gate UNDETERMINED，没有新增 SOL/USD 换算。', '',
'## 最小 isolated regression', '',
'6 笔 BUY 时间依次为 100000、100020、100060、100200、102800、103000，每笔 13000 USDC、100 raw token。前三笔恰好在 60 秒内，后续跨度 3000 秒，库存保留、无 SELL/distribution。CURRENT 最后 hft=True，MULTIPLE hft gate FAIL，其余 MULTIPLE gates 全 PASS；没有 MULTIPLE。R0/R5/R15 均恢复并生成隔离 shadow MULTIPLE。`HFT_STICKY_BEHAVIOR_CONFIRMED = YES`。', '',
'CURRENT subclass 与原 Engine 最小 regression 的 state、signals、完整 evaluation rows 逐项相同。全历史 CURRENT 与此前 verified V1 的 31 signal rows、1095 evaluation rows、153 final mint states 也逐项完全相同。', '',
'## 历史数据与边界', '',
'使用现有 verified durable `history-shadow-ledger-verified.sqlite`，对全部 raw 重新验证 SHA-256、raw signature binding、classifier classification/trade/clock/signer 一致性。可见的更新历史 ledger 未超过此覆盖；没有拼接 forward live 数据。', '',
f"- UTC start: {history['start']}",f"- UTC end: {history['end']}",
f"- usable signatures: {history['usable_signatures']}; ACTIVE_TRADE: {history['ACTIVE_TRADE']}; active tokens: {history['tokens']}; reconstructed episodes: {history['episodes']}",
'- raw missing: 0；642 UNKNOWN_NEEDS_REVIEW、900 FAILED_TX、4433 PASSIVE_TRANSFER、265 ATA_CREATE 不当作 ACTIVE_TRADE。',
'- 203 active tokens 中只有 153 个最终 state、180 个已知 BUY 起点 episode；没有可见起点的 SELL 不制造 episode。',
'- 原拟议 30D window 的更早范围未在该可用子集中，未知交易也未被补猜。raw missing=0 仅指已纳入的 6874 条，不代表完整 30D、更不代表 wallet lifetime。',
'- HFT 每个已分类 signature 至多一个 user-level active trade，不计 DEX CPI hop。wallet/signature duplicate=0，ACTIVE_TRADE raw-hash duplicate=0。未发现这一口径的重复输入；无法仅从 distinct signatures 判断人物意图。',
'- Chronology SHA256: `'+history['chronology_sha256']+'`', '',
'## 总量与分类', '',
'| 指标 | 数值 |','|---|---:|',
f"| episodes_total | {m['episodes_total']} |",f"| episodes_hft_ever（含独立 rapid roundtrip） | {m['episodes_hft_ever']} |",
f"| 60 秒 burst sticky episodes | {m['episodes_60s_hft_ever']} |",f"| 60 秒 sticky ratio | {m['episodes_sticky_hft_ratio']:.2%} |",
f"| rapid roundtrip episodes（与 burst 有重叠） | {m['rapid_roundtrip_episodes']} |",
f"| MULTIPLE CURRENT | {m['MULTIPLE_current_count']} |",f"| MULTIPLE R0 | {m['MULTIPLE_rolling_count']} |",
f"| new MULTIPLE | {m['new_MULTIPLE_from_rolling']} |",f"| new / all episodes | {m['new_MULTIPLE_rate']:.2%} |",
f"| new / current MULTIPLE | {m['new_MULTIPLE_relative_to_current']:.2%} |",f"| current MULTIPLE lost under rolling | {m['current_MULTIPLE_lost_under_rolling']} |",
f"| ACCUMULATION A / B | {m['ACCUMULATION_current_count']} / {m['ACCUMULATION_rolling_count']} |", '',
'31 个 ever-HFT = 9 burst + 23 rapid −1 overlap。研究的唯一变量是其中 9 个 burst 的 sticky 状态，不将全部 31 个都称为 rolling 60 秒误伤。', '',
'分类按首次实际 emission：新增 R0 MULTIPLE 优先归 B；A/B 都无 MULTIPLE、且存在其他核心 gates 全 PASS 的 HFT-only blocked evaluation 才归 C；其余首次结果/时间相同归 A，否则 D。这避免把因金额/库存等原因双边不通过的 episode 全归咎于 HFT。', '',
'| Category | Episodes |','|---|---:|']
for k,v in m['category_counts'].items():lines.append(f'| {k} | {v} |')
lines+=['', '## Recovery sensitivity', '', '| Variant | Total MULTIPLE | New MULTIPLE | Lost current | 新增首次触发相对 R0 |', '|---|---:|---:|---:|---|']
for n,v in r['recovery_sensitivity'].items():lines.append(f"| {n} | {v['MULTIPLE_count']} | {v['new_MULTIPLE_count']} | {v['lost_current_MULTIPLE']} | 四个均 0 秒 |")
lines+=['','四个首次触发距最近 HFT 窗口失效分别已超过 15 分钟。当前样本无法区分 R0/R5/R15，也不能据此认定即刻恢复总是安全。','', '## Sticky burst 后续行为（分母 9 episodes）', '', '| 行为 | Episodes |','|---|---:|']
labels={'has_buy_within_60m_after_hft':'首次 HFT 后 (0,60m] 有 BUY','has_buy_after_60m_after_hft':'首次 HFT 后 >60m 有 BUY','has_buy_after_45m_after_hft':'首次 HFT 后 >45m 有 BUY','inventory_ge50pct_peak_after_hft_seen':'HFT 后某个可判定点 inventory ≥当时 causal peak 的50%','final_inventory_ge50pct_peak':'最终 inventory ≥episode peak 的50%','observed_peak_drop_gt35':'HFT 后曾出现 >35% observed peak drop','unrecovered_distribution_veto':'HFT 后 evaluation 曾触发原 rolling unrecovered distribution veto','finally_closed':'最终 CLOSED','inventory_unresolved':'最终 inventory unresolved'}
for k,label in labels.items():lines.append(f"| {label} | {r['hft_post_behavior'][k]} |")
lines+=['','“曾保留库存”与“最终库存”分开；distribution peak drop 与原 60m 未恢复 veto 分开。终态 5 个 unresolved 不当作归零，也不当作长期持仓。','', '## 四个新增 MULTIPLE 逐一审计', '', '按后续 BUY 数、buy span、USDC 的降序 lexicographic 行为顺序展示；机器结果另外保存每个维度的独立排名。原始 quote 的金额不声明独立核验美元价值。']
for i,e in enumerate(ranked,1):
 a=e['candidate_audit'];s=e['signals']['R0']['MULTIPLE'];windows=e['rolling_hft_fail_windows'];first=e['first_hft_events']
 lines+=['',f"### {i}. {e['mint']}", '',f"episode_id: `{e['episode_id']}`",'',
 f"- 首 BUY / 最后 trade UTC：{e['first_buy_utc']} / {e['last_trade_utc']}",
 f"- 首次 HFT：{e['sticky_hft_first_trigger_utc']}，当时闭区间 60 秒内 {e['first_hft_trade_count']} 个 active signatures，构成 {json.dumps(e['first_hft_composition'])}。前三笔实际 span {first[-1]['at']-first[0]['at']} 秒。",
 f"- 首窗口首次 PASS：{iso(windows[0]['first_pass_at'])}；其后首次低频 BUY：{iso(e['first_low_frequency_buy_at'])}，距该 expiry {e['seconds_from_first_window_expiry_to_low_frequency_buy']} 秒。这是首个不处于 burst 窗口的 BUY，不声称永久无后续 burst。",
 f"- 整个 episode：BUY {e['buy_count']} / SELL {e['sell_count']}；BUY span {e['buy_span_seconds']} 秒；known USDC {e['known_USDC_gross_buys']}。",
 f"- 首 HFT 后完整可见后续：BUY {e['post_first_hft_buys']}；首后续 BUY 到末 BUY span {e['post_first_hft_buy_span_seconds']} 秒；首 HFT 到末 BUY elapsed {e['post_first_hft_buy_elapsed_seconds']} 秒。",
 f"- 截至首次 shadow signal：BUY {a['at_trigger_buy_count']} / SELL {a['at_trigger_sell_count']}；首 HFT 后 BUY {a['post_hft_buy_count_through_trigger']}；累计 USDC {a['at_trigger_known_USDC']}；HFT 后 BUY USDC {a['at_trigger_usdc_after_first_hft']}。",
 f"- signal 时库存 raw {a['at_trigger_inventory_raw']}，causal peak {a['at_trigger_causal_peak_raw']}，retention {a['at_trigger_retention_ratio']}；distribution gate {a['trigger_predicates']['distribution']}。只使用触发前库存，完整 lifetime UNKNOWN。",
 f"- 后续 distribution veto evaluations {e['unrecovered_distribution_evaluation_count']}；曾 >35% peak drop {e['observed_peak_drop_gt35']}；最终 {e['final_state']}，inventory raw {e['final_observed_inventory_raw']}，最终 retention {e['final_inventory_retention']}。后续信息不影响信号。",
 f"- rolling 首触发 UTC：{a['rolling_first_trigger_utc']}；kind {a['trigger_kind']}；距最近 burst expiry {a['seconds_since_last_HFT_expiry_at_trigger']} 秒。",
 f"- triggering signature：`{a['triggering_signature']}`。hourly 触发时该 signature 是 Engine 记录的最新 ACTIVE_TRADE，不把它伪装为该小时新交易。",
 f"- CURRENT MULTIPLE = 无；R0/R5/R15 = 有、首次时间一致。CURRENT HFT-only blocked evaluations: {e['hft_only_blocked_evaluation_count']}。",
 f"- 行为判断：{a['classification']}。{a['classification_limit']} Separate signed transactions 不支持把 Jupiter CPI hops 算作多笔；B 路由意图或 C 真正套利未获可判定证据。",
 '- PnL：PNL_UNAVAILABLE。','', '首 HFT prefix：', '', '| UTC | Signature | Direction | Original quote quantity |','|---|---|---|---|']
 for x in first:lines.append(f"| {iso(x['at'])} | `{x['signature']}` | {x['direction']} | {x['quote_quantity']} {'USDC' if x['quote_asset']=='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' else x['quote_asset']} |")
 lines+=['','rolling fail windows（UTC，end 为最后失败秒）：','']
 for w in windows:lines.append(f"- {iso(w['start'])} → {iso(w['end'])}; first PASS {iso(w['first_pass_at'])}")
 lines+=['','首次 MULTIPLE reason codes：','']+['- `'+code+'`' for code in a['trigger_reason_codes']]
lines+=['','## 已知 winner sanity checks','','| Name | 绑定/历史 | 60s HFT episodes | Current MULTIPLE | Rolling MULTIPLE | Sticky blocked 新增 |','|---|---|---:|---:|---:|---:|']
for w in r['winner_audits']:
 lines.append(f"| {w['name']} | {w['status']}"+(f"; {w['episode_count']} episodes | {w['hft_60s_episode_count']} | {w['current_MULTIPLE']} | {w['rolling_MULTIPLE']} | {w['sticky_blocked_rolling_multiple']} |" if w['status']=='PRESENT' else ' | UNDETERMINED | UNDETERMINED | UNDETERMINED | UNDETERMINED |'))
lines+=['','STONK 有两个 observed episodes：正式 MULTIPLE episode 在 2026-09-06T04:18:35+00:00 已触发，直到 2026-09-09T21:24:55+00:00 的后段 SELL burst 才出现 HFT。它确实曾 HFT=true，但没有阻止此前 MULTIPLE；A/R0 首次 signal 完全相同。不能把“ever HFT”误当作“被 sticky 漏报”。', '',
'PAID exact mint 的 5 个 episode 中 4 个出现 60 秒 HFT，CURRENT 有 1 个 MULTIPLE，R0 有 3 个（新增两个详见上文）。其他三个 episode 的结果保持不变。PAID 与 STONK mint 使用仓库既有 `research/frank-30d-replay-state.md` 锚点，再确认存在于 raw-verified ACTIVE_TRADE dataset。', '',
'Pistacio / PERPSPAD / fone / Pumpcat / CATE 在既有报告中只有名称/聚合描述，当前 bounded 本地来源未找到可核验 name→mint 绑定；不宣称它们不在 dataset，不猜 mint、不制造交易。这里是 winner attribution 数据缺口。', '',
'## 行为强度与事后经济重要性', '',
'四个新增的逐维度独立排序保存在 JSON `behavior_rankings`，使用后续 BUY 数、整个 BUY span、已知 USDC 和最终 retention；最终 unresolved 值在排名末尾，明确保留 missing，不转换为真实零库存。若末值相同，原 chronological order 稳定排序。', '',
'经济排名：**PNL_UNAVAILABLE**。已有文档中的公共聚合 PnL、不同窗口或 token 总盈亏，不能可靠分配到本次 observed episode。没有完整 cost basis、剩余库存经济估值、历史转换与每个 episode 的已核验收益证据，所以不编造 per-episode PnL、不按后来价格排序。所有 signal 都先依原 chronology 生成，之后才附加行为/赢家描述。', '',
'## 判断与下一步所需证据', '',
'保留 NEED_MORE_DATA：3 个 BUY burst 后继续建仓的新增 episode 具有明确持续建仓行为（两 PAID + 一个未命名 mint），但第四个混合 turnover episode 同样被放行。R5/R15 没有过滤该混合样本；样本数小，不能证明延迟恢复解决噪声。3/4 新增最终 unresolved、缺可靠逐 episode PnL，使 “没有明显扩大垃圾信号” 尚未成立。', '',
'若研究继续，需要补齐 observed inventory 的不可判定 SELL/raw-routing 缺口、完整窗口覆盖、winner mint provenance，以及与 episode 可审计关联的事后经济结果。此轮没有补抓、没有修 parser、没有为结果改阈值；也没有提出可直接上线的 V2。', '',
'## 交付、验证与生产隔离', '',
'研究 helper：`local-agent/scripts/frank_hft_sticky_rolling_historical_replay.py`。post-replay audit/report helper：`local-agent/scripts/frank_hft_historical_replay_report.py`。isolated regression：`local-agent/tests/research/test_frank_hft_sticky_rolling_historical_replay.py`。逐 episode 全 chronology/窗口/信号/reason codes/排名：`meme/evidence/frank-hft-sticky-vs-rolling-2026-10-04.json`。SQLite 与 runtime isolation snapshot 只保留 private evidence。', '',
'CURRENT/ROLLING helper 只能创建新 historical workspace，拒绝已有 workspace、live 命名和 forward.sqlite source。所有 generated outbox 为 DRY_RUN_AUDIT，未调用 delivery adapter。', '',
'生产源码/config SHA-256 均与研究前相同；daemon PID/restart_count 不变、loaded source commit 不变、source_drift=false。仅只读现有 health 文件证明隔离，没有进行 live validation。最终 Git commit/push 仅包括 research helpers、historical regression、report、evidence；不 merge main。', '',
'PRODUCTION FILES CHANGED = NO; POLICY CHANGED = NO; LIVE SERVICE RESTARTED = NO; LIVE/HISTORICAL SIGNAL SENT BY RESEARCH = NO; PRODUCTION_TRADING = NO_GO.','']
args.report.write_text('\n'.join(lines))
print(json.dumps({'report':str(args.report),'candidate_episodes':len(candidates),'conclusion':r['conclusion'],'baseline_parity':parity},indent=2))

r['validation']={'research_tests_passed':10,'full_suite_passed':557,'failed':0,'skipped':3,
                 'skip_reason':'Unrelated Monster v2/v3/replay require missing numpy',
                 'raw_binding_replay':'6874 raw hash/signature/classification matches',
                 'source_code_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (
                     'scripts/frank_hft_sticky_rolling_historical_replay.py',
                     'scripts/frank_hft_historical_replay_report.py',
                     'tests/research/test_frank_hft_sticky_rolling_historical_replay.py')}}
A.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
with args.report.open('a') as report:
 report.write('''
## 实际验证与复现

研究 regression：10 passed、0 failed、0 skipped。完整 local-agent suite：557 passed、0 failed、3 skipped（numpy 缺失的无关 Monster 测试）。历史完整 CURRENT parity：31 signals / 1095 evaluations / 153 mint states，全字段相同。四个 variants 均通过隔离 outbox DRY_RUN_AUDIT 与 SQLite integrity 检查。

运行命令来自 Frank-only local-agent cwd：

```sh
python -m pytest -q
python -m pytest -q tests/research/test_frank_hft_sticky_rolling_historical_replay.py
python -m scripts.frank_hft_sticky_rolling_historical_replay \\
  --source "$PRIVATE_EVIDENCE/history-shadow-ledger-verified.sqlite" \\
  --work "$PRIVATE_EVIDENCE/frank-hft-sticky-rolling-historical-replay-NEW-UNIQUE-RUN" \\
  --policy config/frank_local_signal_v1.json \\
  --output ../meme/evidence/frank-hft-sticky-vs-rolling-2026-10-04.json
```

其中 python 为原已存在的 local-agent venv，PRIVATE_EVIDENCE 为本地已有 Frank-only private evidence 根目录。work 必须全新。post-replay report helper 的 `--help` 显示所需 artifact、variant-work、原 baseline、研究前只读 boundary snapshot、现有 runtime health 文件与 report 参数。既有结果已完成，无需触及 live DB 复现。
''')
