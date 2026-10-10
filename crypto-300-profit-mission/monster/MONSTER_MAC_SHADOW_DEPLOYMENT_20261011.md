# Monster V4 与 Frank 并行的本地 Shadow 部署操作

状态：安装器和回归测试在 GitHub CI 中通过。**未在用户 Mac 安装或验证成功。** 本文命令只部署公开行情的研究 Shadow，不启用真实 Gmail、自动买卖、端口监听或现有 Frank 的配置变更。

## 1. 前置条件

macOS，git 已配置 GitHub 仓库的读取权限，Python >=3.9。建议新建完全独立的 Monster checkout `~/Documents/ChatGPT/monster-v4-shadow`，**不要切换 Frank 当前所在的工作树/分支**。源码读取原 PR #30 分支 `research/monster-v4-local-discovery-20261010`。

首次安装（以下为 zsh 可直接执行命令，代码块内无注释）：

```zsh
mkdir -p "$HOME/Documents/ChatGPT"
git clone --single-branch --branch research/monster-v4-local-discovery-20261010 https://github.com/lxxlx2/ChatGPT_mission_record.git "$HOME/Documents/ChatGPT/monster-v4-shadow"
MONSTER_INSTALLER="$HOME/Documents/ChatGPT/monster-v4-shadow/crypto-300-profit-mission/local-agent/scripts/monster_v4_mac_service.py"
python3 -B "$MONSTER_INSTALLER" preflight
python3 -B "$MONSTER_INSTALLER" install
python3 -B "$MONSTER_INSTALLER" status
```

如果独立 checkout 已存在，不要重复执行 clone；在该 checkout 内执行 `git pull --ff-only`，然后运行 preflight/install/status。若系统仅安装旧 Python，请先选择本机已有 Python >=3.9 的实际二进制。**不要将脚本与 Frank 的 existing SQLite/LaunchAgent 捆绑，也不要复制 Frank 的 token/密码到此模块。**

首次运行数据库是空的；一个轮询周期后查看数据是否出现。后续报告准确性依赖官方 API 在 Mac 所在的网络环境是否可达。

## 2. 服务与数据隔离

- LaunchAgent label：`com.chatgpt.crypto-mission.monster-v4.shadow`
- Plist：`~/Library/LaunchAgents/com.chatgpt.crypto-mission.monster-v4.shadow.plist`
- 数据库：`~/Library/Application Support/MonsterV4Shadow/state/monster.sqlite`
- stdout：`~/Library/Application Support/MonsterV4Shadow/logs/shadow.stdout.log`
- stderr：`~/Library/Application Support/MonsterV4Shadow/logs/shadow.stderr.log`
- 源码发布：`~/Library/Application Support/MonsterV4Shadow/releases/<code-hash>/`
- 间隔：180秒一次；开启时首轮立即拉官方 Spot + USD-M 全市场。SQLite 存储 WATCH/D1/D2、健康、全部 DRY_RUN_ONLY outbox。
- 无自定义端口；Frank 的 Dashboard 端口 8766 / Frank LaunchAgents 均**不修改**。

可选状态/证据检查（同样不需要手工修改配置）：

```zsh
MONSTER_INSTALLER="$HOME/Documents/ChatGPT/monster-v4-shadow/crypto-300-profit-mission/local-agent/scripts/monster_v4_mac_service.py"
python3 -B "$MONSTER_INSTALLER" status
launchctl print "gui/$(id -u)/com.chatgpt.crypto-mission.monster-v4.shadow"
tail -n 20 "$HOME/Library/Application Support/MonsterV4Shadow/logs/shadow.stdout.log"
tail -n 20 "$HOME/Library/Application Support/MonsterV4Shadow/logs/shadow.stderr.log"
launchctl list | grep -Ei 'monster|frank'
```

如果 `status` 显示 `LOADED`，但缺少最新 poll、stdout 停更或出现 spot/futures API 错误，**还不能宣称运行健康**；按真实日志分辨 Python、权限、429、地理网络限制、时间戳、交易所响应问题。前瞻14日 shadow 需要监控各 venue `last_poll`、覆盖缺口、D1/D2积压、重启去重、预期变动/实际通知事件。

## 3. 保守回滚

```zsh
MONSTER_INSTALLER="$HOME/Documents/ChatGPT/monster-v4-shadow/crypto-300-profit-mission/local-agent/scripts/monster_v4_mac_service.py"
python3 -B "$MONSTER_INSTALLER" uninstall
python3 -B "$MONSTER_INSTALLER" status
```

`uninstall` 只移除 Monster 的 LaunchAgent，**保留 Monster SQLite、日志及历史发布目录**，不会触碰 Frank。若另一个程序使用相同 plist label，则安装/卸载拒绝修改。

## 4. 状态和权限

本命令激活本机公开行情 `shadow-loop`，不需要用户私钥/交易API/Gmail凭据。真实移动端/邮箱通知仍未启用；正式通知必须独立完成消息分级、去重、过期、Gmail授权、实际发信与 Sent readback 后才能标记为已送达。用户此前只授权研究与未来本地部署，未据此授权自动交易；`PRODUCTION_TRADING=NO_GO`。

交付者远程无权操作 Mac 设备；用户提供本机安装的 `status` 与必要日志后，才可以把本地部署状态由 `NOT_DONE` 调整为 `VERIFIED`。GitHub Actions 模拟安装成功≠本机安装成功。
