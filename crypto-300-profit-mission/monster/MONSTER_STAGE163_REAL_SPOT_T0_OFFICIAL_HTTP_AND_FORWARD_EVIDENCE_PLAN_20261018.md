# Monster Stage163 — Binance Spot 原始 HTTP 点时市场 T0 已取得；未来同venue OOS/净盈利证明路线（2026-10-18）

## 一、这轮真正取得了什么（不是模拟，也不是旧2月回放）

用户明确询问是否能自主取得数据并继续。已**一次性只读**从 Binance 官方无密钥公开市场API `https://data-api.binance.vision` 采集，不创建任何自动化或定时任务。原有Stage99手动停止规则仍有效，Frank、Mac生产/通知/交易均不触碰。

- 第一批连接器结构化观察：2026-10-17T21:54:43.469Z，客户端请求区间 `21:54:43.082Z…21:54:55.601Z`；`/api/v3/exchangeInfo?permissions=SPOT`原结构化3689身份，USDT725，其中TRADING511、BREAK214，511/511交易对能关联顶层正价BBO。Git `evidence/monster_stage163_spot_manual_t0_20261017T215443Z/` 保存全部身份、725条完整交易规则分片、所有实时BBO及BTC少量分钟/24h源可行性探针；13个源文件Git blob SHA均已读回核对。注意本批是**连接器结构化返回、无HTTPS原响应字节和原SHA**，不能冒充下面新一批官方原始字节；两批相差约10分钟，不许把它们当同一时刻。
- **新的正式原HTTP T0**：[GHA #39073557939](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39073557939)，显式一次请求SHA `a0dfda1a6a14bb08c36afa4c67f15bd7088ac4cb`，2/2 job success，官方文档支持无API key市场专用域名：https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md 。交易所 `exchangeInfo.serverTime=2026-10-17T22:04:40.094Z`（曼谷2026-10-18 05:04:40.094）。真实采集6端点的HTTP响应体**原字节**：`/api/v3/time` before/after、`/api/v3/exchangeInfo`、`/api/v3/ticker/bookTicker`、`/api/v3/ticker/24hr`、`/api/v3/depth?symbol=BTCUSDT&limit=100`，源接收完成于2026-10-17T22:04:48Z附近。该6端点不是同一纳秒同刻，仅受before/after时钟和GitHubCI收包时间约束。
- 原始HTTP源已**永久压缩提交 Git**：`evidence/monster_stage163_spot_original_http_t0_actual/source_raw_http.zip`（压缩包592,022 bytes）及同目录`source_receipts.json`（每个源的URL、抓取UTC、HTTP Date、MIME、原体字节数和SHA256）。原zip SHA256 `b47e206345c0a04b16b37c38795d726553ef83ca679f443f9fba89805483216b`；原GHA Artifact ID **12116091492**（另存，可至2026-12-16T22:04:49Z），raw zip历史Git副本不会因Artifact到期丢失。未使用中文来源站点或私钥。
- 本对话从GHA真实Artifact重新下载、解两层ZIP，独立算`SHA256(source_raw_http.zip)`，6个内嵌`*.response.raw.json`字节SHA与receipt逐个相等：**6/6 MATCH**；不是只相信源代码的print。原源 `exchangeInfo` 17,767,696字节SHA `4c04abd88caeae5613977e0f5e2a5044efaeb557dc7e7fbd5bba0d03a5794493`，24h ticker 1,912,204字节SHA `7f3dd27e8c83bdbff80f9ec3d99feac99636113308a0bdef603730ee87aef31e`。
- 新原始全市场 `exchangeInfo` 包含**3729交易对**（TRADING1380、BREAK2349），对比前一批按`permissions=SPOT`筛选的3689少40，是**接口参数人口范围不同**，不是结果冲突。USDT Spot资格725（TRADING511、BREAK214）。511/511目前活跃USDT对都具有正价非交叉买卖顶层BBO、及24h ticker回执；BTCUSDT另有真实当时盘口100档bid/100档ask，仅证明此瞬间单符号深度可取，并不表示已经保存所有511币的L2或未来退出深度。
- 原字节独立描述性质量统计（定义`spread_bps=20000×(ask-bid)/(ask+bid)`；经验分位数取排序后index floor((N-1)×p)）：活跃511的p10/median/p90顶层价差约 **2.0608/11.217/28.9715 bps**，24h quoteVolume USDT p10/median **59,489.3218/464,067.9191**，顶层bid/ask名义挂单`price×qty`中位约 **332.8142/357.5098 USDT**。注意这些不是有订单就一定可成交、不能把报价深度乘积当作流动性承诺/实际成交、不是回测P&L。独立QA见 `evidence/monster_stage163_spot_official_http_t0_20261018_qa_actual.json`。
- 首次source selftest [GHA #39073460225](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39073460225) 只因合成源只造300条但全市场阈值设1000而测试失败，尚未连接API，已保留失败记录；改为1100合成后正式第二轮全真实Source成功。**不得将第一次失败说成官方HTTP源失败**。

## 二、冻结这次真正新的Spot时间窗口（非旧USD-M窗口）

新的Spot source T0源交易所时间为 `2026-10-17T22:04:40.094Z`；首个允许在T0之后产生的新3min D0 tick为 **`2026-10-17T22:06:00Z`**，按固定3m tick研究完整7日的右开区间 **`[2026-10-17T22:06:00Z, 2026-10-24T22:06:00Z)`**，共3360轮。对应曼谷2026-10-18 05:06 到 2026-10-25 05:06。不可把窗口内不存在的未来数据现在当成已取得，尤其不能用T0以前的24h rolling涨跌幅当作未来上涨。

按原D0策略所需至少24h先验回看与7日右开，官方**Spot** daily 1m档案最少涉及`2026-10-16…2026-10-24`共9个UTC交易日；公开`data.binance.vision` daily ZIP+发布者CHECKSUM在相应交易日结束后陆续发布，需后续合格源审计（Binance官方 https://github.com/binance/binance-public-data/blob/master/README.md 说明2025-01-01后Spot归档时间戳为**微秒**，切忌按USD-M毫秒处理）。真实可完整评分必须等最后一天档案和publisher SHA实到、价源齐全，参考最早**2026-10-26（曼谷）后再核查实际发布情况**，这不是自动采集日程，也不保证当时已经齐全；**只在用户以后主动发消息授权时手动采集**，不创建定时任务。

本次官方HTTP T0能**真实锚定起点活跃511USDT Spot人口**，但没有连续七天的现时`!contractInfo`/Spot交易对变更收包，故G0当时初始人口`T0_ASOF_PROVEN`，全窗口含新挂牌/停牌恢复`G0_COMPLETE_7D=PARTIAL`。今后必须对511个T0 eligible符号每个创建attempt，缺档`CENSORED`不算0信号，窗口内新挂牌不悄悄添加到T0分母；可单列`LATE_LISTING_UNVERIFIED`。不能拿今天这份原HTTP Spot当作2月445币当时的完整PIT清单，也不能把Stage91/92先前**USD-M**的窗口当成Spot Fair8样本外。

## 二点五、七日窗口不阻断Monster主线开发（2026-10-18，持续交接优先级）

**这个七日窗口仅是 Stage163-S 的固定观察样本边界，不是 Monster 开发、回测、Review、功能交付的前置依赖。** 起点由2026-10-17T22:04:40.094Z官方 Spot T0实际收包后，取下一个3分钟整点2026-10-17T22:06Z而来；取7×24小时=3360轮形成右开区间。曼谷10月25日05:06只是样本终点，10月26日以后检查原始daily ZIP是否齐全只是档案可得性检查，均无策略上的神奇阈值。**不得到期就宣称策略自动通过。** 原V4架构还要求在满足前置门禁、得到安装授权后另行做至少14日真正连续 shadow；这一七日官方历史分钟档案重放不能替代实时服务/通知时延验证。

**独立研究主线现在就可推进，按实际业务价值排序，并保留有依赖的强制工程顺序：**

1. **策略价值和历史结果总审计**：固定原D0/D1与Stage162 FIFO8/Fair8，对照已暴露445/758、原有六日期的漏报、失效、旧资金账本亏损和新SETUP=0，列出造成不能转化为可交易机会的主要环节；严禁把Stage162新增27个有效首评记成新增盈利交易，不再针对同一固定SHA重复形式化审查。
2. **可执行的历史跨日期压力测试**：利用已有、或新自主取得并校验官方publisher ZIP的**未拿来选该次规则**日期，完整回放共享D0/D1/8槽，显式报告全市场分母及新上市/退市缺证据，时间不重叠也不能冒充真PIT时标记 `HISTORICAL_DATE_DISJOINT_CAUSAL_PROXY`；即使数据源不足以支持真OOS，也能验证主流程完整性、队列功能和基础发现价值。
3. **D2/模拟交易闭环**：从历史已合法出现的 WATCH/SETUP 出发，报告当时可观察的现货资格、实际报价时间、价差、成交额、到期/追涨判定。费用/资金量可研究参数化情景，但用户单笔金额/费率未给仍标 `UNKNOWN`；没有同一信号时点以及预注册退出时点双向足额盘口，真实可成交净PnL坚持 `NOT_SCORABLE`，不得以高低价或现今盘口充当。
4. **功能性最小端到端验收**：隔离使用原代码链路和持久事件，验证全市场D0→候选队列→D1→D2→一条可读的WATCH/SETUP/失效研究输出，展示发现时间、当前时效、场所、可操作性与数据缺口。仅本地/CI研究 dry-run，不接真实通知/交易，不修改Frank或建立计划任务。重点解决会让正常用户错过机会的实际问题，停止无收益意义的无限边界测试。
5. **本次固定七日样本成熟之后**，追加独立同venue 511起点USDT Spot 的3360轮FIFO8/Fair8报告，包含原SETUP保留、新增/丢失SETUP、漏报、延迟、删失及费用数据缺口。分钟出版ZIP只能产生 `OFFICIAL_1M_CAUSAL_PROXY_STRESS`，没有真实时点24h ticker、持续listing变更和动态L2时，完整PIT、真实通知和交易G4不得升级。

**产品成功定义**：用户能在币开始异动时及时看到可解释且不过期的WATCH，强信号升级有成交条件证据，漏报/待评价队列/无效或过时机会可回溯，且在有足够真实证据时可证明扣成本的交易价值。若严格样本外/净收益验证失败，应明确记录 `FAIL/NO_GO`，基于主要业务根因重新设计策略；不得继续靠微调同一已暴露样本、增加研究阶段编号或反复复核低价值边界来伪造完成。Stage162研究批准继续有效；新实质代码变更必须经过其自身测试和真正独立审查。

**授权边界不变**：手动公开来源获取由用户聊天触发；无后台采集、无GHA schedule、无新ChatGPT Automation/launchd、无Gmail、无交易，Frank保持隔离。当前 `G4 UNKNOWN`、`G6 NO_GO`、`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。

## 三、如何真正证明交易价值（预注册、可证伪，不因结果再改口）

在窗口成熟后，用**同一Spot原D0和真实研究V2 D1、原FIFO8与固定SHA `b85dee96ec6f567e1f0b90f0d50cc5b19c79018b` Stage162 Fair8**，在511起始群体真实官方分钟源上按当时已闭合数据做同源3360 tick A/B。输出一条条WATCH身份/首次有效评价/升级`SETUP_ACTIVE`、有效期内与LATE状态、原SETUP保留和失去/新SETUP及确切触发时间；不可看未来高价或2x标签来决定当时选择优先级。注意历史publisher分钟档案**不能重建当时交易所精确24h实时ticker或真实消费者收到通知的UTC**，若D0依赖了重建24h代理，只能记为`OFFICIAL_1M_CAUSAL_PROXY_STRESS`，不是原实盘系统全源PIT逐条信号等价。真实持续ticker24/盘口动态与送达验证仍缺。

盈利测量必须**逐笔冻结后验退出规则**，在实际通知之后入场的原始卖盘ask深度及未来确定平仓时原始买盘bid深度中，以用户明确的研究名义订单金额、真实现货lot/tick/minNotional、实际当时可用fee tier、滑点、未成交与价格冲击计算，不许买在K线最低价/卖在未来K线最高价，也不得把同时刻ask→bid摩擦成本当成七日净利润。实测仓位资金金额/手续费tier目前未给，保持`USER_AMOUNT_UNKNOWN/FEE_TIER_UNKNOWN`，可以先做无交易的覆盖与流动性可用性研究，**不要求API key、不要求下真单**。沿用Stage149 G4门槛：≥30个时间与方向一致、完整有Bid/Ask深度的研究可执行场景、现金流和风险回撤可重算，否则`G4 UNKNOWN`；公开历史Binance分钟ZIP无法反推原始历史盘口L2，也不能伪造现成30例。实际成交需经真实用户授权且有交易回执，本阶段绝不交易。

本次只冻结T0与数据准入。独立外部Review已完成的Stage162研究代码不重新审；新增Stage163只读source捕获器/真实执行本次CI通过，**它本身的独立其他AI源码Review=NOT_DONE**，不会因此改变生产放行。真正需要下一轮model审查时一并核查新时间源和独立A/B核心，避免再陷入反复审核无盈利价值的边界。

## 四、Git/current gate 与最小用户配合

源脚本`local-agent/scripts/monster_v4_stage163_spot_one_shot_raw_http_source.py`、仅响应单份手工request的`.github/workflows/monster-v4-stage163-spot-original-http-t0-once.yml`、实际请求`monster/source-batches/monster_stage163_spot_original_http_t0_request.json`、真实Git原字节证据和本记录均已归档到原Monster Draft PR #30，不动生产/Frank/邮件/交易，也**无任何GitHub schedule/cron/launchd/ChatGPT Automation**。

**现在用户不用提交个人文件或账户权限**。将来要从`研究可执行场景`进一步判断真净收益时，仅需明确一个用于模拟的**每笔名义USDT金额**、现货**手续费档位**（或允许按保守场景计算），无需任何密钥、钱包助记词或券商账户授权。在拿到真实对应时点双向盘口以前，也不急于收这些信息。

截至2026-10-18：`STAGE163_SPOT_REAL_ORIGINAL_HTTP_T0=PASS_SOURCE_BYTES_SHA_VERIFIED`，`SPOT_T0_UNIVERSE=511`，`SPOT_7D_FORWARD_RESULT=NOT_MATURE`，`FULL_7D_LISTING_CHANGE_FEED=UNKNOWN`，`FAIR8_NEW_SETUPS_IN_TRUE_FUTURE=UNKNOWN`，`G4 UNKNOWN`，`G6 NO_GO`，`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。

## 五、现有D0/D1/D2研究机会查询器：代码与回归实际通过（2026-10-18）

这是一次**现有SQLite上游代码不变**的实用功能交付，用于使使用者读懂当前Shadow持久化的WATCH→SETUP→D2研究状态；不升级旧策略阈值，也不改变Stage162算法/历史样本。新代码：`local-agent/scripts/monster_v4_opportunity_snapshot.py`，配套：`local-agent/tests/test_monster_v4_opportunity_snapshot.py`。

- 固定代码/测试及workflow提交：`5a54ef90823c4e8f51b8fed557de4fbd6c44a1b1`。基线：上一轮研究计划变更 `51fcf066ef144d1526146a952e6b190961092a3a`。
- 实际GitHub CI：[Monster V4 Research Baseline #39075413068](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39075413068)，`historical-baseline` job **SUCCESS，22/22 steps complete**；新增真实D0/D1/D2 SQLite生命周期测试 **8/8 PASS**；同次CI原Shadow与D2模块回归通过。
- 读取方式：`python3 -B crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py --db /ACTUAL_MONSTER_SQLITE_PATH --format text`，需要可访问已存在的**独立研究SQLite**，不自动创建数据库；也支持 `--format json` 输出明确带 `NO_GO` 的研究数据。路径仅为命令占位示意，未要求用户现在安装或提供私有数据；实际Mac仍未部署。
- 只读SQLite URI `mode=ro` 与 `query_only=ON`；代码无Binance HTTP、无Gmail、无定时、无下单。关联原持久队列episode、准确SETUP event key、D2 review/source evidence，区别WATCH、SETUP、失效、迟到、15m过期、source陈旧、合约专属；同时显示最后已存报价及时间，**报价不是当前市场执行价**。
- `SETUP_ACTIVE` 历史事件持久存在不能永久当成可跟进信号；超过原15m deadline的即`EXPIRED`。D2的`research_liquidity_gate`仅为历史研究当前盘口摩擦代理，金额若显示30U属于旧研究假设、不是用户授权金额，始终输出`RESEARCH_REVIEW_ONLY_NO_BUY` / `G4 UNKNOWN` / `G6 NO_GO`。指定`--asof-ms`仅用于在**已存在状态**上计算年龄，不能倒推其时真实数据库状态或冒充因果回放。
- 这是**合成SQLite端到端功能测试**及GitHub runner验收，尚无真实用户Mac上部署/实时连续场景/通知送达，新的查询器独立其他AI审查仍`NOT_DONE`。历史Stage30负资金结果和Stage162新增SETUP=0均没有被新功能改变。下一价值主线继续针对可执行性、信号时效、真正独立时间样本和风险；不得因这8个测试绿灯认定模型盈利。

现有`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`与手动采集规则不变。
