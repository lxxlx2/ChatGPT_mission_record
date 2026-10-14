# Monster Stage133：按真实用户手动请求完成取数后冻结新T0，前瞻源入口代码与离线测试

2026-10-14 Asia/Bangkok，原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。本轮只实现研究数据入口；**尚未真实请求一份新的当前官方行情**，没有发布新的未知窗口，未来 G1/G2/G3/G4 完全未过线。不会修改旧 Stage105/116 与 Stage118/127 的冻结失败结论、阈值、资金门槛或已曝光样本。

## 1. 原模型风险决定下一步优先级

[Stage132 原31币真实历史数据复算](MONSTER_STAGE132_ORIGINAL31_FIRST_SIGNAL_PRICE_PATH_NEGATIVE_HISTORICAL_RESULTS_20261014.md) 已确认：新上市研究通道19个首次动量信号，以额外延迟一分钟、价格按下一根分钟 OPEN 进入且零成本，预设15m/1h/6h/24h四档**毛收益中位全为负**，分别 -2.5681% / -3.9260% / -4.8253% / -3.2593%；多数信号亏损价格代理。后验 2× 高点不等于买卖能赚，**既有“首动量即买”研究方案只保留为 D0 研究，不可继续买入部署**。不准在旧31上换阈值寻找成功。

阻碍真正有效模型的主要根因之一是原 Stage105/116 三个固定前瞻窗口首个 **2026-10-14 06:00 UTC** 的 source `SOURCE_FAILED_NO_BACKFILL`；后来 Stage123 09:48 的市场快照虽然有效，却不能证明06:00原窗口来源。没有实时信号过程、没有完整中途上新分母及实际交易资格/深度，不能用一小时后补抓改善旧 G1。Stage131 已经提供了将初始全市场与随后上新合约分开的离线人口桥接。

## 2. 解决正式前瞻起点脆弱性的唯一新取数契约

**先冻结再写代码**：[Stage133 合同](MONSTER_STAGE133_FROZEN_MANUAL_FORWARD_ACTUAL_T0_PROVENANCE_PROTOCOL_20261014.md) 已在任何新 CI 之前提交 commit `ebd50073b8fc27b5cb0dd8c00bf7e0a8d741f42c`。

独立 [Stage133 Python 实现](../local-agent/scripts/monster_v4_stage133_manual_actual_t0_forward_proof.py)，新增原生安全验证：
- 唯一入口只有用户未来明确请求后准备的 `--capture-request`，必须为 `MONSTER_STAGE133_USER_REQUESTED_ONE_SHOT_V1` 且 `explicit_manual_request=true`。单纯运行无 request 必须拒绝，模块引入不会访问网络，CI 也绝不采新行情。
- 每次真正执行时，顺序读取 Binance 官方 HTTPS `/fapi/v1/time`、`/fapi/v1/exchangeInfo`、`/fapi/v1/time`，保存原始返回字节解码文本、SHA256、请求和回应端真实机器时间，以及两次独立官方 `serverTime`。校验 URL、原始内容哈希、有效 Binance 时钟 ±5s、时钟和三次 GET 的顺序。**交易所 exchangeInfo 的 serverTime 不用于时钟证明。**
- 保留所有状态的完整 ExchangeInfo；精确 Unicode symbol 去重，活跃 `TRADING/PERPETUAL/USDT` 的 venue-only 名录单列。即使某个合约是 Equity 或未来不能实际成交，原 source 仍保留，币种发行身份、合约量纲和 Spot 可买性单独 `UNVERIFIED`。
- 未来 7 天 T0 采用事先冻结的确定性计算 `(floor(最后一次官方time结束的机器毫秒/300000)+2)*300000`：取数全部结束后 **严格再留5至10分钟**，开始一个真正新的 7 天实验源时钟。每个实验必须有自己的真实三源完整读回及未来全市场上新/退市/分钟证据，不自动创建三个日历任务，也不修改原 Oct14/28/Nov11 Stage116 固定日期。没有完整未来源时 `PENDING_WINDOW_END` 和 `G1=NOT_SCORABLE`。
- **重要来源级别限制**：三份 TLS 抓取源的哈希和订单日志只能证明保存文件自洽，离线任意文件本身没有 Binance 数字签名，不可把纯本地合成fixture或个人伪造 JSON 升级为独立官方时点认证。正式真实取数后仍需证明实际取数环境、来源URI和过程；Spot/发行Crypto身份与真实成交仍是 G0/G4 后续要求。

## 3. 已做而未做

[Stage133 GitHub Actions #38587686275](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38587686275)，代码 HEAD `e2c35d7a8b1729731fde18347bcdc5c6eee8ef1c`：

- macOS job `115933943530` **SUCCESS**；
- Ubuntu job `115933943773` **SUCCESS**；
- 7项离线确定性单元测试（合成原始双独立time源、以后正式的5至10分钟起点、完整/非活跃及Unicode标的、请求明确授权、SHA被篡改拒绝、时钟颠倒/漂移拒绝、后验exchangeInfo.serverTime忽略、拒绝用无time的Stage123代理）；软件编译测试均成功；
- CI 另以**实际CLI**不传手动授权请求运行，验证它拒绝网络取数与输出文件，不创建任何后台任务。

这些是工程测试完成，**真实的新独立 G1 验证窗口尚未开始**，因用户尚未单独发起真正的手动新采集，且即使之后取得完整T0，仍需未来168h真实来源及最少三段互相独立完整 Crypto 市场窗口、20个独立2×事件的统计验证。

## 4. 实际后续研发顺序

1. 保留 Stage132 的经济代理 NEGATIVE，停止在已见31个样本寻找新的盈利阈值。
2. 将 Stage133 一次性真实 T0（仅用户未来明确聊天触发）同 Stage131 完整两车道的 cohort ledger 及 Stage116 G1 评价器衔接，但不得让原 Stage116 的固定时间口径被重写为新的验证日期。新的三次完整前瞻必须独立预登记、没有人工优选涨幅或换日期。
3. 每个完整未来七日事件复盘须保留新的上市币、未触发D0的普通币及后来被删失的真实人口，只有确认Crypto身份、独立交易时点和源才评分 G0/G1；中途上新按上市后的首根有效分钟并单列，不与老币 anchor 开盘倍数混合。
4. 策略 D1 只有在新数据足够且单套候选的门槛先冻结后测试时才继续新策略验证。G4 须用户指定名义金额及实际真实 bid/ask 盘口、真实手续费与保守退出条件，至少30个独立完整样本，现保持 UNKNOWN。待策略与源全部过线、其他AI真正独立Review完成后才能申请 Mac 独立 Shadow 的用户批准。

`STAGE132_HISTORICAL_PRICE_PROXY=NEGATIVE_DONE`; `STAGE133_CODE_AND_TEST=PASS`; `STAGE133_LIVE_NEW_CAPTURE=NOT_DONE`; `STAGE133_REAL_NEW_OOS=NOT_STARTED`; `STAGE116_OLD_FIRST=SOURCE_FAILED_NO_BACKFILL`; `G0=PARTIAL`; `G1_NEW_OOS=NOT_SCORABLE`; `G2_G3=NOT_PASSED`; `G4=UNKNOWN`; `OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOY=NO_GO`; `GMAIL=OFF`; `FRANK=UNCHANGED`; `NO_NEW_SCHEDULE`.
