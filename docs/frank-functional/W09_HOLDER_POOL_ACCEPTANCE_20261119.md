# W09 持有人供给与池候选核对

[PR #253](https://github.com/lxxlx2/ChatGPT_mission_record/pull/253) 的安装源码为 `15edc5060d586550e642ca2737824e5dd7628df6`，父提交为 `9cd954636599ab8003c7dca97c35372c2c767fa7`。本轮修复和本地验收通过。W09 全量来源覆盖仍为 **PARTIAL**，生产与交易为 **NO_GO**。

## 修复和反例

- 供给快照要求同一 finalized slot，或由权限生效槽位及同量的前后供给覆盖枚举槽位。后取得的 Mint 状态可作为较新的供给起点，但不能为更早的枚举背书。旧实现会在权限晚于枚举、权限字段缺失，以及 Token-2022 可能关闭或扩展资料无法核实的夹逼案例中误报完整排名。旧归档保留原数据，页面按当前证据规则展示。
- 单个 Owner 读批失败后继续核对剩余批次，并保留失败批的未知身份。超时或位置冲突不能转成普通钱包。旧实现遇到第一个失败批次就退出元数据循环。
- 合并全部已观察的索引、Owner 和 Mint 过滤池候选。目标 Mint 在计价侧时仍作池候选，并保留目标币行情未取得的状态。按 RPC 的 100 地址上限分批，记录每批 finalized slot、响应摘要与安全失败原因。任一批缺失时保存其他批结果。金额排除要求池与持仓位于同一 finalized slot；分批后槽位不一致的池仍保留结构证据。测试覆盖 105 个池、12 个已读 Owner 池线索、首批超时、同槽与跨槽反例。
- 已有来源的字节上限与协议发现范围保留。超出单次传输约束会保留来源缺口。全网池全集、全量 CEX／做市／锁仓身份、独立同槽复核及所有协议版本的原始储备仍待补证。

[Solana Mint 权限](https://solana.com/docs/tokens/basics/set-authority) · [Token-2022 Mint 关闭](https://solana.com/docs/tokens/extensions/close-mint)

## Mac 与 Chrome 实测

隔离服务与安装后的 Dashboard 都使用原端口 8766。Chrome 通过「查看输入 CA 的历史报告」读取合成报告。105 条池候选全部出现在页面，分 2 个批次，未选 0 条。安装后读取真实旧归档，其中 1 份旧报告的夹逼记录缺少权限槽位。当前实现将它的全局 Top10 显示为「未确认」。两项是合成流程和真实归档回放。另两份真实旧归档缺少全局枚举与多池身份审计，三份都不能支撑完整 W09。W10 的钱包历史及控制归因项目在一份归档中为部分覆盖，另两份未记录该完整性条目。

安装档的 648 个跟踪文件逐个对照 Git blob。先恢复并读取旧版，再启动候选版。安装后核对静态文件、运行目录和旧成本账本，Scanner PID 与受保护控制文件摘要相符。Chrome 标签停留在已安装的本机只读报告页。本轮真实 RPC、CA 作业、通知、签名及交易调用均为 0。GitHub workflow 查询当时无该源码 SHA 的 PR 运行记录。

## 回归命令

在固定提交的 detached checkout 内进入 `crypto-300-profit-mission/local-agent`，用已存在的 pytest 开发环境运行以下命令。新增夹逼条件的历史回归夹具随验收记录更新，部署程序和已验证的 `15edc5060d586550e642ca2737824e5dd7628df6` 一致。

```sh
PYTHONDONTWRITEBYTECODE=1 python - -q -p no:cacheprovider --tb=short \
  tests/test_meme_holder_ranks.py tests/test_meme_holder_binary.py \
  tests/test_meme_wallet_cluster.py tests/test_meme_wallet_cluster_pagination.py \
  tests/test_meme_ca_completeness.py tests/test_meme_pool_vaults.py \
  tests/test_meme_pool_holder_roles.py tests/test_meme_special_roles.py \
  tests/test_meme_no_pool_roles.py tests/test_meme_global_pool_discovery.py \
  tests/test_meme_owner_pool_discovery.py tests/test_meme_market_and_rpc.py \
  tests/test_meme_market_parity.py tests/test_meme_owner_history_gaps.py \
  tests/test_meme_narrative_story.py tests/test_meme_narrative.py \
  tests/test_narrative_supplement.py tests/test_meme_first_buy_completeness.py \
  tests/test_frank_ca_job_rpc_budget.py <<'PY'
import sys
def offline(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname', 'socket.sendto'}:
        raise AssertionError('offline test attempted network access')
sys.addaudithook(offline)
import pytest
raise SystemExit(pytest.main(sys.argv[1:]))
PY

node --test --test-reporter=tap \
  tests/test_frank_ca_get_resume.mjs tests/test_frank_ca_rpc_budget_ui.mjs \
  tests/test_frank_ca_report_render.mjs tests/test_frank_d2_ingress_ui.mjs \
  tests/test_frank_f01_source_only.cjs tests/test_frank_f01_failure_state.cjs
```

Mac 通过 **588 项 Python、233 项 Node**。Chrome 隔离和安装后实测独立于上述回归与 CI。
