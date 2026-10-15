# Monster Stage150 — 实际原始525合约交易过滤规则定量研究（2026-10-15）

原 Monster Draft PR #30；按长期开发规则，先冻结[Stage150 原始数据/原 Stage120规则研究协议](MONSTER_STAGE150_FROZEN_REAL_525_EXCHANGEINFO_TRADE_RULE_READINESS_PROTOCOL_20261015.md)（commit `efb81d45598b6a28b5c9e5dd99416e607a50fa17`），再开发和真实数据测试。本阶段不是 G4 胜率，也不是用户批准下单。

## 输入链和范围

**已有真实保存资料**，不是今天新拉取的行情：Stage140 于 2026-10-14 17:52Z 左右从 `www.binance.com` FAPI 网站镜像取得 exchangeInfo 及一套全部市场 bookTicker、24h ticker、mark；原始三次 HTTP+SHA/时间和原始525人口通过已完成 Stage148 Codex独立代码 `APPROVE@41f58cd3a1bde8d9b01cffc74f04ae36f26685aa` 的 `stage147.audit()`。Stage150 **先调用 stage147.audit() 完整验证真实 Stage133→139 原始来源和525合约、三份market wrapper，随后直接解析原始 Stage133 exchangeInfo `raw_http_records.official_exchange_info.raw`**。每一个原始币调用已经冻结的 `monster_v4_stage120_exchangeinfo_execution_rules.parse_filters(raw_symbol)`，没有复制策略或另外重写过滤规则。

固定源 exchangeInfo 原 raw_sha: `ccdde257bdb19900aaef2d0dc572ed0e7f8f30cf0d3e35bf115bd72ddc4d0849`. 网站镜像对标准 `fapi.binance.com` 的完整等价与源时间**未独立证明**；镜像内嵌 serverTime 的已知落后约 **31,452,652 ms（约8h44m）** 不可当实时合约合法性保证。

## 真实全市场运行结果，不是猜测

GitHub Actions Stage150 工作流将本仓库保存的原始真实源从磁盘加载，Ubuntu 和 macOS 运行同一源码，打印完全一致的 Python JSON：

| 真实来源+历史规则项目 | 实测 |
|---|---:|
| 原始初始美元本位活跃USDT永续合约人口 | **525/525** |
| `underlyingType=COIN`，发行主体未独立证明 | **523** |
| `underlyingType=INDEX`，不记实币G1 | **2** |
| 官方 `underlyingSubType` 声称包含 `Crypto` | **524**（和523 COIN不是等义数据、不能作为发行者真实性） |
| 官方 `underlyingSubType` 声称包含 `Meme` | **46**（只是场所类别，不是已证实可盈利妖币） |
| `baseAsset` 文本以1000或1000000等开头，需要另行核实资产单位 | **11**（名称特征，不是合约倍数已证实） |
| Stage120 `COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION` | **525** |
| Stage120 缺失 / 无效 `LOT_SIZE/MARKET_LOT_SIZE/PRICE_FILTER/MIN_NOTIONAL` | **0**（只对本保存时点的这些声明字段） |
| 有最低名义金额过滤规则 | **525** |
| 最低名义额规则中位数 / P90 | **5 / 5** quote units (USDT 声明) |
| MARKET_LOT_SIZE step 中位数 | **1** 原声明数量单位 |
| LOT_SIZE step 中位数 | **1** 原声明数量单位 |
| 独立验证发行者身份 / 合约倍率 / 实际成交 | **0 / 0 / 0** |

这一结果回答了核心研究问题：Stage140初始全量交易所合约的**已保存基本过滤规则全部可解析**，因此不应再将“缺失MARKET_LOT_SIZE”当成525市场的主要广泛数据障碍。真正瓶颈是 `issuer` 和 `unit` 的独立证实、未来WATCH时点资格、入场和退出两套真实时间匹配L2/费用、真实消息收到时钟。没有任何币因过滤规则完整就升级为可执行或正净收益，最小名义金额5不是用户的交易金额、不是最小所需保证金、也不是全订单必定能成交。

注意 `underlyingSubType=Crypto` 524条可能包括 INDEX；不能与 `underlyingType=COIN` 523条混淆，也不能做G1真实20个Crypto事件的身份凭据。11条1000前缀只是原始 `baseAsset` 的**名称模式**，并不是合约乘数或链上数量兑换的已验证结果。

## 实际代码、测试、跨系统CI

新增文件：
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage150_real525_exchangeinfo_trade_filter_readiness.py`
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage150_real525_exchangeinfo_trade_filter_readiness.py`
- `.github/workflows/monster-stage150-real525-original-trade-filter-offline.yml`

**固定可审核源代码 SHA = `e569dddccddf12736051534f2bf0b56b0329ad62`.**

[真实 GitHub Actions #38706943546](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38706943546) finished **SUCCESS**, pin `e569ddd...`。Ubuntu job `116328578669` 与 macOS job `116328578333` 各自读取 Stage140 原始2.5MB Stage133 exchangeInfo，与已保存的525条三份市场original HTTP、Stage147来源链、Stage120原parser做全套校验，实际日志：

- Ubuntu: `Ran 14 tests in 3.696s` `OK`
- macOS: `Ran 14 tests in 2.258s` `OK`
- 两者打印完全相同原始市场 `counts` 与 `filter_rule_measures`，`STAGE150_REAL_RAW525_STAGE120_FILTERS_NO_FAKE_G4=PASS`，`STAGE150_NO_LIVE_GET_NO_SCHEDULE_NO_GMAIL_NO_TRADE_NO_FRANK_NO_DEPLOY=PASS`。
- 集成的14条包含Stage150 5条和Stage147 9条；Stage150覆盖真实525全量、旧Stage148源篡改必须拒绝、Stage120规则缺失不得升级COMPLETE，以及默认无资金金额、无盈利认证。
- 无新行情GET、没有GitHub cron、launchd、Mac生产部署、自动交易、Frank修改和邮件。

**Stage150 独立新 SHA 源码审查尚未收到**；旧 Stage148 CodeX `APPROVE@41f58cd...` 不自动审核新增Stage150文件，按开发规范已经提供完整另一AI复审提示词。新代码只是交易所元数据研究与时间窗口外受限的字段解析，不提供 BUY、真实利润。单币字段 `actual_fill=NOT_OBSERVED`、`net_executable_profit=UNKNOWN`，所有525 `G4_verified_executable_case=false`。

## 下一项真正能改变模型收益结论的证据

1. G1 需要来源完整、独立样本时间点的真实七日前瞻出版社1m窗口和合法crypto首次2x总体，Stage140窗口结束2026-10-21 18:00UTC（按原规则延迟48h后另由用户明确手动请求采集）。没有真实上市事件`!contractInfo`的连续用户收报时刻，不可声称已证实的零发现延迟或后验OHLC就是实际WATCH。
2. G4 需要同一WATCH+D1**后**可看到的逐档L2（entry）和未来exit时刻逐档L2、独立单位/发行主体、合法市场数量/价格step和MARK规则、用户明确的研究金额、双方手续费/资金费用，至少30独立案例才有可核实的建模机会；仍不得称模拟L2是实际交易所已成交回执。
3. 直接沿用原Stage90 D2真实盘口验算和Stage120规则；不再重复开发独立来源包装，不改变原D0/D1。现有2025年的305历史D1样本都没有相应时间点完整L2，不可用2026年的525一次性快照替代。

**门禁严格维持** G0 PARTIAL, G1 NOT_SCORABLE, G2/G3 NOT_PASSED, G4 UNKNOWN, G5 new Stage150 independent code review NOT_DONE (old Stage148 peer APPROVED@41f58 only), G6 NO_GO; original Stage116失败、Stage118/127 rejected、Stage132 chasing negative; original PR #30仍Draft, NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE，Frank unchanged，Stage99仍停止，未来采集必须用户主动要求。
