# Monster Stage 6 — 实际 Binance 盘口执行成本与 Mac Shadow 部署验证

日期：2026-10-11 Asia/Bangkok  
状态：D2 策略级模拟和全流程代码已落 Git，真实冻结盘口已经回放；Monster 邮件发送未开通、Mac 安装待本机验证、独立其他 AI 审查待完成；自动交易 NO_GO。

## 1. 为什么加入 D2

前面 Stage 3/4 证明纯粹的突破/放量信号不能直接盈利。Stage 5 发现历史赢家与普通信号的前态差异，但样本事后标注且并非独立前瞻验证。本阶段解决另一个实际问题：即使 WATCH/SETUP 正确，用户计划每笔仅动用约30 USDT时，当前盘口是否真能买卖？实际费用/滑点/交易量限制是否会使理论利润不可达？

计算路径：`D0 首次 WATCH → D1 后续完整5m确认 SETUP → D2 官方 Spot 100档盘口与 exchangeInfo交易规则 → 30 USDT taker 买入 → 假设买入手续费从base扣除 → LOT_SIZE保守取整 → 同一盘口立即以bid卖出 → 再计假设卖出手续费`。

**这只是独立时间点快照的即时往返成交成本估计**：盘口随时撤单，快照非原子，不能证明以后能成交，更不能表示买入胜率或预测收益。手续费每边暂用 **10 bps (0.1%) 的情景值**，不是用户已核实的 Binance 实际费率，也未对可能的 BNB 折扣作默认假定。

### 实际3组冻结官方盘口（非合成数据）

来源：Binance Spot `/api/v3/exchangeInfo?symbol=...` 和 `/api/v3/depth?symbol=...&limit=100`，2026-10-10 20:55:47 UTC（曼谷时间 2026-10-11 03:55:47）；两次API不是同一时刻的原子快照。原始交易规则、100档 bids/asks、lastUpdateId、采集时间均保存在 [证据 JSON](evidence/monster_stage6_spot_orderbook_3symbol_20261011.json)。具体数字由 [官方盘口回放脚本](../local-agent/scripts/monster_v4_d2_evidence.py) 用 [Decimal 模型](../local-agent/scripts/monster_v4_d2.py) 对冻结数据计算，已在 [CI #38085969964](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38085969964) 实际运行。

| 交易对 | 最优买/卖报价（bid/ask） | BBO价差 bps | 30 USDT瞬时往返成本 USD | 往返成本 bps | 100档深度可模拟完全成交 |
|---|---|---:|---:|---:|---|
| TSTUSDT | 0.01785000 / 0.01787000 | 11.1982 | 0.093701235 | 31.233745 | YES |
| BROCCOLI714USDT | 0.02459000 / 0.02462000 | 12.1926 | 0.10389603 | 34.63201 | YES |
| BTCUSDT | 83056.70000000 / 83056.71000000 | 0.0012 | 0.129488412 | 43.162804 | YES |

注意：即使 BTC 的 BBO 价差极小，小额30 USDT买入、再按保守LOT_SIZE交易量取整后卖出也产生可见的额外成本。只观察价差而忽略数量精度会低估机会的实际门槛。成本结果包含显式假设手续费，且可能因实际钱包手续费付款资产而变化。三组均通过**仅用于研究的快照流动性门槛**（价差<=100bps，瞬时往返成本<=250bps）；这并不等于推荐买入。

更需要的是真实历史/前瞻 `WATCH→D1→D2` 全链路 D2 入场时价差、费用、24h实际路径的分布。不因三次可成交样本直接推广到妖币整体、保证及时成交或声明策略净正收益。

## 2. Git 已交付功能

- `../local-agent/scripts/monster_v4_d2.py`：交易所状态校验、盘口单调性/交叉检查、交易规则、30USDT按价档扫单买卖、显式费率情景、可执行性/阈值及清晰 `RESEARCH_LIQUIDITY_NOT_BUY` 分级。可单次以现行官方接口运行；不使用用户认证API。
- `../local-agent/scripts/monster_v4_shadow.py`：D1 SETUP事件加入新 SQLite `d2_reviews` 独立可持久化队列。仅 Spot 请求现货盘口；合约设置 `D2_NOT_SPOT`；盘口错误按退避重试；超过10分钟记录 `D2_LATE`，不得补作当前买入建议。循环每轮限量深查，不丢失其余积压记录；所有发送仍只入 `DRY_RUN_ONLY`。
- `../local-agent/scripts/monster_v4_d2_evidence.py`：冻结真实数据严格回放，CI直接输出每个例子的精确指标；不会向 Binance 下单。
- `../local-agent/scripts/monster_v4_mac_service.py`：Mac 独立发布目录、LaunchAgent `com.chatgpt.crypto-mission.monster-v4.shadow`、180秒独立扫描间隔、独立 `~/Library/Application Support/MonsterV4Shadow/` 下的 SQLite/logs。支持 `preflight` / `install` / `status` / `uninstall`，卸载保留证据数据库，不触碰 Frank 的 plist、路径或端口。实际激活必须在用户 Mac 执行，不存在远程静默安装。
- `tests/test_monster_v4_d2.py`、`tests/test_monster_v4_shadow.py`、`tests/test_monster_v4_mac_service.py`：真实冻结证据回放与合成异常回归，包括浅流动性、昂贵整币取整、深查重试、过期停止、仅合约不会标现货、LaunchAgent与Frank隔离及回滚。

## 3. 本地与 Frank 并行的运行合同

Monster 代码、运行进程、状态、日志、启动项和未来通知 outbox 必须**全部独立**。新服务没有自定义端口，没有密钥要求，不能读取/修改 Frank 的数据；启动不自动交易也不发送 Gmail。发布后需要在用户机器通过 `launchctl print gui/UID/com.chatgpt.crypto-mission.monster-v4.shadow`、独立数据库 polls/health/logs、实际成交源覆盖率、重启去重、恢复机制逐项验证，不能仅凭plist存在认定在线。

Shadow 初步运行至少覆盖14个自然日，记录首次WATCH的发现时滞、D1/D2队列积压、D2深度/真实取整费用，以及连续多日429/API响应异常。**当前 CI 使用冻结数据和模拟器，不是Mac本机真实连续运行。**

安装前和安装后都保留所有 Frank 既有服务、不创建重名 LaunchAgent、不使用其数据库或消息队列。若用户仅执行 `preflight` / `status`，不会安装。 `install` 是明确的本地用户授权操作， `uninstall` 删除本模块 plist 且保留数据库/日志。

## 4. 仍未过线的放行要求

| 项目 | 状态 | 证据/限制 |
|---|---|---|
| 真实3组现货 orderbook / exchangeInfo 保存 | DONE | 冻结 JSON、Decimal 回放及 CI |
| D0→D1→D2 持久队列代码 | DONE（代码/合成测试） | 尚未运行用户机器的真实前瞻集成 |
| Frank/Monster Mac 隔离安装与回滚 | DONE（脚本/单元测试） | 本机实际安装与进程验证 NOT_DONE |
| 独立其他 AI Review | NOT_DONE | 未获得有身份与版本锚点的独立审查意见 |
| 14日真正 forward shadow 与漏报调查 | NOT_DONE | 无本机长时间运行证据 |
| 真实通知（授权后）/Gmail Sent readback | NOT_DONE | 现阶段仅 DRY_RUN_ONLY |
| 稳定净收益与真正可执行交易 | UNKNOWN/NO_GO | 没有前瞻策略证据，自动交易不授权 |

下一优先顺序：独立review → Mac预检/Shadow安装并验证Frank共存 → 前瞻采集/修复API状态/延迟问题 → WATCH到D2多日收益与漏报归因 → 正式通知用户授权后真实发送+送达回读。不能把完成上表代码项偷换成通过全部门槛。
