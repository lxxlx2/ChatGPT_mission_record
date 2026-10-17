# Monster Stage163 — 独立时间源、Spot/USD-M隔离、PIT/G4可执行证据关口预注册（2026-10-18）

## 输入与新的研发目的（先定数据准入，再运行任何模型）

Stage162仅通过了2026年2月已曝光、445/758源完整Spot历史样本的同8槽公平调度机制实验，独立Codex审核通过固定`b85dee96ec6f567e1f0b90f0d50cc5b19c79018b`，**新增有效5m首评27、净新增SETUP=0、原120 SETUP保留，尚无真实盈利**。Stage163要验证的是独立未来市场里同样策略是否真正**早于潜在行情出现、产生新增可执行SETUP和净收益**，不是把已经验证过的27个首评当成27笔交易。

**现有事实及禁止跨场所误归因：**
1. Stage162算法数据是**Binance Spot** 1m分钟数据与V4 `spot` 原队列身份，February 2026，事后挑选源完整445/758、另313源缺失、当时`quote24`是历史代理。即使另取交易日完全独立，也不能以**今天**的Spot listing快照冒充那日真实PIT全市场；只能叫`HISTORICAL_DATE_DISJOINT_STRESS_NOT_TRUE_PIT_OOS`。
2. 已冻结Stage91/92真正前瞻七日窗口是**Binance USD-M**，窗口`2026-10-14T06:00Z..10-21T06:00Z`、`2026-10-28T06:00Z..11-04T06:00Z`、`2026-11-11T06:00Z..11-18T06:00Z`；它们采用旧USD-M Stage38/Stage80 D0/D1，**不是本次Spot Stage162选中调度**。不准把USD-M G0/G1/G2/G3通过说成Spot Stage162 OOS通过，除非另建立点时正确的交易场所和同一策略共享回放合同并独立验证。
3. Stage91首个窗口起点 `2026-10-14T06:00:00Z` 先前Stage99数据未采到、固定`SOURCE_FAILED_NO_BACKFILL`；Stage123取得`2026-10-14T09:48:24.840Z`的新USD-M结构化快照和Stage140独立更晚的真实源，**都不能回填6点原起始人口证明**。截至2026-10-18，10-14→10-21七日窗口仍未结束，后续七日2×/5×事件和获利退出标签尚不能宣称完整。Oct28/Nov11是**仅用户主动聊天触发**参考日，不能新建GHA schedule/launchd/cron/ChatGPT Automation。
4. Git已保存的Stage123 USD-M 525活跃USDT PERPETUAL、793滚动24h tickers、795 BBO、930 mark和五个Unicode符号，**不是** Spot data；Stage90和Stage120有两侧L2/过滤规则，Stage149查实完整旧历史bid/ask depth通常拿不到，不能仅凭某日期OHLC/aggTrade或旧USD-M BBO推导Spot当时可执行净收益。未指定的用户名义资金金额始终`UNKNOWN`，不能凭旧案例擅选$30/$100/$300。

## 两条严格独立、不相互替代的数据路线

### 163-S：未来Spot点时市场人口+真实闭合5m公平调度

- **首次有效的新Spot研究起点必须在实际采集时确认**：保存`GET /api/v3/exchangeInfo`**完整原始HTTP字节**、合法响应身份/HTTPS来源、请求与接收UTC、服务端时间（若有）、原始SHA256、所有交易symbol状态与quoteAsset、contract flags不适用；不能把USD-M `/fapi/v1/exchangeInfo`混进来。无法提供真实原响应字节，只能`PARTIAL_AS_OF_SOURCE`；不能伪造官方checksum或T0。
- 现时点新币/停牌/下架、确切精确symbol（Unicode）和USDT Spot是否真正在当时可交易要保留**全population尝试表**；仅靠事后仍活跃的symbol当前名单=survivorship-bias，不能把缺源样本算作0 WATCH/0盈利；完整PIT上市变更stream若缺失，G0仍部分未知。
- 使用同一历史原D0/原V2研究零quote D1和新Fair8选择策略，在**独立未来采集完成**后按真实3m/5m时钟、8槽、真实15m deadline对原FIFO8与Fair8同源A/B。保留逐候选`first_seen/first_valid_eval/SETUP_ACTIVE`及一切失败，分别报告总WATCH、重复、迟到、SETUP保留、新增、原SETUP丢失、延迟、UI适合候选。禁止用事后获利币筛选、改变既有Stage162优先权定义或搜索最佳门槛再称OOS。
- 单次T0快照或手动T1对比只允许`SNAPSHOT_PAIR_GROSS_MIDQUOTE_PROXY`；**不能**证明3m/1m历史通知真实接收时刻、真实WATCH、首达2×，更没有Spot真正部署/实时采集。源需要用户单次手动明确触发，未来符合授权之后再开发真正本地运行方案。

### 163-U：既有USD-M Stage91/92三前瞻窗口（独立原有主线）

- Stage91/92的`G1>90%提前2x`等门槛只针对原版USD-M模型，不把新Spot Fair8的Stage162结果移植到该USD-M策略或当作G2通过。
- 真正人口PIT快照必须在原各窗口T0前15min内归档，窗口中新上市或恢复交易的contractInfo当时收包也必须归档；没有这些时`G0_PARTIAL`，即便后续下载所有官方daily 1m ZIP也不能补成原T0 PIT。
- 原3个7日窗口最后到2026-11-18；其中10-28和11-11原来的手动参考日期为**用户未来主动要求**，不是自动采集约定。除非有完整当时源、窗口成熟、候选身份/未收包缺口和所有分母，否则`FRESH_OOS_COMPLETE=NOT_DONE`。

## 必须先拿到的真实证据和拒绝放行条件

| 关口 | 目前可验证源 | 现状 | 下一次合格证据 |
|---|---|---|---|
| Stage162 Spot历史机制 | 445 Spot February，Codex固定SHA审核，原始Artifact A/B全SHA | `DONE_RESEARCH_ONLY` | 无须再重复该审核 |
| Spot未来PIT全人口/变更 | 无已核的首次新T0 Spot原HTTP及窗口内变更全部保真归档 | `NOT_DONE` | 用户主动单次真实采集+原SHA/接收时点+新旧人口attempt |
| Spot未来3m WATCH→D1真实观察 | 无原Spot未来窗口完整分钟档与当时通知接收日志 | `NOT_DONE` | 当时原始来源包+同源双队列回放；真送达需要另行授权 |
| USD-M既定3窗 | Stage91/92源码和Stage123/140其它UTC的真实USD-M源 | `G0_PARTIAL` | 对每窗单独证明原T0及窗口内listing变化，缺证据就Block |
| 历史交易可执行净PnL | Stage90/120测试源/Stage149实源缺口；有些现时刻BBO但非同候选时点双边L2 | `G4_UNKNOWN` | ≥30真正点时完整准入/入场后和预定退出双侧盘口，明示研究名义金额及费率/滑点/funding；不冒充实际成交 |
| 当前授权 | Stage99已用户终端readback取消，PR30 Draft，不发信不交易 | `NO_GO` | 不擅自恢复定时任务/部署；未来用户额外明确授权 |

官网数据源：https://github.com/binance/binance-public-data ，该官方仓库README明确 Spot **2025-01-01之后的历史ZIP成交K线时间戳采用microseconds**，官方day ZIP与同目录`.CHECKSUM`可验证发布归档；这一SHA保证归档完整性而不证明当时上市人口/PIT HTTP，不能拿历史分钟ZIP中的sym目录推断完整当时市场列表。USD-M数据毫秒/Spot微秒的单位转换必须留在各自已审核source adapter，禁止串场；本阶段没有下载新Spot源或产生新的市场结论。

## 执行与唯一下一项有价值工程任务

- 本文件只冻结**数据选择与业务验收**，不要求立即再写一个重复的D2成本引擎、下载多年所有代币ZIP、对已经曝光Feb445重新回测、或为了小边界不断请求独立代码Review。
- 优先核对**已经有真实原始T0的完整当时source**中，是否存在可为新模型提供独立时间验证的`spot` source，若无则明确`SPOT_OOS_PIT_T0_NOT_ARCHIVED`。另在用户明确手动发起下一次Monster公共数据采集时，保持原USD-M原始四源流程，同时**独立增加Spot source路径需新范围确认**；两者的生命周期不能拼接。
- 如能获取与某个已冻结策略同场所的完整真实官方分钟ZIP与T0早于研究结果的原始source记录，先建立source completeness/冒充PIT的fail-closed gate，再实际跑原FIFO8 vs Stage162公平8且必报全部新旧SETUP/延迟和成本缺口。**没有真PIT证据必须降级报告，而不是造假的OOS盈利结论。**
- 可使用`BINANCE_PUBLISHER_ZIP_SHA_VERIFIED_HISTORIC_DATE_DISJOINT`标签对不同时期事后Spot kline做**独立日期机制回归**，但严禁把它标为真正全PIT人口预测。真实网络历史L2缺口与资金金额UNKNOWN导致G4一直UNKNOWN；不能以历史正收益门槛跳过这些。

截至2026-10-18：
`STAGE162_EXTERNAL_REVIEW=CODEX_APPROVE_RESEARCH_ONLY`
`STAGE163_SPOT_TRUE_PIT_OOS=NOT_DONE`
`STAGE163_USDM_3WINDOW_G0=PARTIAL`
`STAGE163_G4_REAL_EXECUTION=UNKNOWN`
`G6=NO_GO`
`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`
