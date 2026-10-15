# Stage150 直接复制给 Claude / Codex 的完整独立审查提示词（固定SHA）

你继续担任 Mission Monster 妖币研究模块的**独立第二AI代码审核员**。请实际 checkout 固定代码 SHA，复测真实保存的 Binance exchangeInfo，不要只复述开发报告，更不要因为旧Stage148批准就自动批准新的Stage150脚本。

**仓库** https://github.com/lxxlx2/ChatGPT_mission_record
**原 Monster Draft PR #30** https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
**分支** `research/monster-v4-local-discovery-20261010`
**本轮固定需要审核的Stage150工程SHA** `e569dddccddf12736051534f2bf0b56b0329ad62`
**已获外审通过但只覆盖旧源码的Stage148 SHA** `41f58cd3a1bde8d9b01cffc74f04ae36f26685aa`
**前一轮Stage147被拒的SHA** `e6ec373d00e368d249758d6887a4a5144afd7ae9`

必须说明你的审核身份/确切模型版本（无法独立证实就写 `UNVERIFIED`），真实检出并保留上述源码SHA；如果PR HEAD因文档提交向前走，不要以浮动HEAD冒充固定代码审查。

第一部分：阅读以下原始材料、源文件和工作流：
- `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`
- `crypto-300-profit-mission/monster/MONSTER_STAGE150_FROZEN_REAL_525_EXCHANGEINFO_TRADE_RULE_READINESS_PROTOCOL_20261015.md`（在代码前已冻结）
- `crypto-300-profit-mission/monster/MONSTER_STAGE149_G4_REAL_EXECUTION_SOURCE_FEASIBILITY_AND_MODEL_NEXT_ACTION_20261015.md`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage150_real525_exchangeinfo_trade_filter_readiness.py`（新代码）
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage150_real525_exchangeinfo_trade_filter_readiness.py`（新测试）
- `.github/workflows/monster-stage150-real525-original-trade-filter-offline.yml`（新无定时工作流）
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage120_exchangeinfo_execution_rules.py`（冻结原 `parse_filters`，LOT/MARKET_LOT/MIN_NOTIONAL逻辑，不应重写）
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage147_saved_real_bbo_execution_readiness.py`（Stage148已过Codex来源真实性校验，Stage139→134→133验证原始525）
- 原 Stage140 Git source 目录：`crypto-300-profit-mission/monster/evidence/monster_stage140_user_authorized_real_www_mirror_20261015/t0_2026-10-14T175247096Z/` 的 `stage133_original_three_HTTP_T0.json`、`stage139_original_T0_asof_contract_metadata.json`、`stage140_evidence_manifest.json`、BBO/24h/mark三份包装。

第二部分：真正检查 Stage150 是否完整遍历**保存的全部525原始场所USDT永续**，没有漏掉 INDEX/Unicode/普通币，只读保存Stage133原始 exchangeInfo raw，且所有 source/三市场 raw SHA、时间、接口与原始完整525逐行身份由Stage147原 audit验证。Stage150 是否原样调用Stage120.parse_filters，而没有暗中替换、放宽 MARKET_LOT_SIZE、价格步长、交易所不同种 MIN_NOTIONAL 规则？是否忽略 filter 缺档，把 `TRADE_RULES_PARTIAL_OR_INVALID` 误改为 `COMPLETE`？逐一核对至少原始 525=523 `underlyingType COIN` +2 INDEX、525全部 Stage120 `COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION`，`underlyingSubType`文字包含 `Crypto` 有524，`Meme` 有46，`baseAsset`文本以1000或1000000开头计数11，MIN_NOTIONAL源声明中位/第90百分位均是5USDT，数量步长中位1。注意524 Crypto subtype**并不等于**真实发币币种个数；2 INDEX和523 COIN不能错混。11是命名特征而不是合约倍率证明，`quantityPrecision`不是stepSize。

第三部分：严格质疑**交易可行性**的过度解读。此真实来源于 2026-10-14 17:52 UTC WWW Binance 网站FAPI mirror的保存单次原始快照，标准fapi同源与市场真是时刻尚未独立证明，exchangeInfo内嵌serverTime比真实采集落后31,452,652ms（约8小时44分）。基本过滤元数据525/525完整不能证明后来 D0/D1 的交易资格、发行主体、合约规模、订单有效/最低保证金、盘口多档成交、bid/ask价差成本和在未来退出；305条历史D1没有对应时间L2，也不能拿Stage140一次BBO补。禁止由于metadata完整将 `G4_verified_executable_case`改True、实际成交 `actual_fill`改FILLED、净利润UNKNOWN改正，甚至偷偷设任何默认用户300 USD交易金额。可复核输出所有525都 `NOT_OBSERVED`/`UNKNOWN`/G4 UNKNOWN。

第四部分：运行固定源码真实CI和在自己的环境复测：
- https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38706943546 （GitHub head SHA 为 `e569dddccddf12736051534f2bf0b56b0329ad62`），Ubuntu job116328578669、macOS job116328578333 **各14/14 PASS**，都在原始保存真实525数据上执行，并检查 `STAGE150_REAL_RAW525_STAGE120_FILTERS_NO_FAKE_G4=PASS`、无GET/定时/Gmail/交易/Frank/部署。
- 在固定SHA的 `crypto-300-profit-mission/local-agent/scripts` 目录运行：
`python3 -B -m unittest -v test_monster_v4_stage150_real525_exchangeinfo_trade_filter_readiness.py test_monster_v4_stage147_saved_real_bbo_execution_readiness.py`
`python3 -B monster_v4_stage150_real525_exchangeinfo_trade_filter_readiness.py --out /tmp/monster-stage150-review.json`
- 用独立小样本测试 Stage120.parse_filters 在 `filters` 缺失、一个市场数量规则缺失/重复、非法 MIN_NOTIONAL 与完整源相反时是否 fail closed 不给COMPLETE；改变派生525或原 raw时旧Stage148 gate继续拒绝。
- 在报告中自行校验 `original_source_venue_counts` 汇总、`filter_invalid_reason_counts` 和一组真实逐币MARKET_LOT_SIZE/最低名义值。任何新数据下载（尤其2026-10-14以外报价）不能冒充当时 as-of 数据。

最后返回：审核模型身份与版本、固定 SHA、实际运行环境及测试、`APPROVE / REQUEST_CHANGES / BLOCKED` 代码结论、发现的 P0/P1/P2（源文件和行号、可执行输入/实际与预期、对早期妖币可交易盈利误报的影响、最小修复方案）。没有实质问题不要凑数量。完整保留 Stage116原始06:00源失败不可回填、Stage118/127拒绝、Stage132追涨负收益研究；G0 PARTIAL、G1 NOT_SCORABLE、G2/G3 NOT_PASSED、G4 UNKNOWN、G6 NO_GO。此次代码无论APPROVE与否，**PR仍Draft, NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE**，Frank不变，Stage99停止，手动采集10月28/11月11安排不变。独立代码审核APPROVE不等于模型盈利或实际净成交验收。
