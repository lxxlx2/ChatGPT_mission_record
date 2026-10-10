# Monster V4 与 Frank 并行的本地 Shadow 部署操作

**状态更新 2026-10-11：部署被正式撤回并锁定为 `DEPLOYMENT=NO_GO`。当前不应安装 Monster，包括本地 Shadow。** 原先版本的安装命令已过早提供，违反数据→策略→技术方案→实际V4历史回测→其他AI审查→修复测试→部署的顺序。任何历史上复制的 install 命令也将由当前安装器拒绝执行。

## 1. 何时才会开放本地部署

严格遵守 [Monster 模块开发规则](MONSTER_MODULE_DEVELOPMENT_RULES.md) 与 [回测重做审计](MONSTER_V4_MODEL_BACKTEST_REMEDIATION_20261011.md)：

1. 全市场历史数据与分钟级真实数据已核验、能重放V4真实WATCH/D1判断。
2. 完成策略设计、技术设计，并用相同V4生产逻辑完成历史事件回测/噪声成本研究；不合格返回策略设计。
3. 其他AI基于同一commit和真实回测产物完成独立Review；修复重大问题并重测通过。
4. 上述证据作为Git签署的合格gate后，安装器代码新提交由NO_GO变更为GO，才能批准在Mac与Frank并行部署。

目前未达到2、3，安装器 `DEPLOYMENT_GATE="NO_GO"`；因此**本阶段不提供或推荐执行任何本地安装命令**。Mac隔离设计、日志位置、回滚行为等细节仅供将来审查，不构成部署许可。

## 2. 服务与数据隔离

- LaunchAgent label：`com.chatgpt.crypto-mission.monster-v4.shadow`
- Plist：`~/Library/LaunchAgents/com.chatgpt.crypto-mission.monster-v4.shadow.plist`
- 数据库：`~/Library/Application Support/MonsterV4Shadow/state/monster.sqlite`
- stdout：`~/Library/Application Support/MonsterV4Shadow/logs/shadow.stdout.log`
- stderr：`~/Library/Application Support/MonsterV4Shadow/logs/shadow.stderr.log`
- 源码发布：`~/Library/Application Support/MonsterV4Shadow/releases/<code-hash>/`
- 间隔：180秒一次；开启时首轮立即拉官方 Spot + USD-M 全市场。SQLite 存储 WATCH/D1/D2、健康、全部 DRY_RUN_ONLY outbox。
- 无自定义端口；Frank 的 Dashboard 端口 8766 / Frank LaunchAgents 均**不修改**。

以下状态检查命令为将来通过放行门槛后的本地验收材料，并非当前要用户执行的任务。暂不需要本机操作。

## 3. 保守回滚的设计约束（待通过门槛后验证）

未来 `uninstall` 仅可删除本模块的LaunchAgent，保留数据库和日志，不得停止、更改Frank服务；既有用户环境需实机证据验证。当前无需卸载（本轮尚未在用户Mac部署过Monster）。

## 4. 状态和权限

未来经批准的安装才会激活本机公开行情 `shadow-loop`，不需要用户私钥/交易API/Gmail凭据。真实移动端/邮箱通知仍未启用；正式通知必须独立完成消息分级、去重、过期、Gmail授权、实际发信与 Sent readback 后才能标记为已送达。用户此前明确要求研发闭环完成之后才在本地部署，未据此授权自动交易；`PRODUCTION_TRADING=NO_GO`。

交付者远程无权操作 Mac 设备；用户提供本机安装的 `status` 与必要日志后，才可以把本地部署状态由 `NOT_DONE` 调整为 `VERIFIED`。GitHub Actions 模拟安装成功≠本机安装成功。
