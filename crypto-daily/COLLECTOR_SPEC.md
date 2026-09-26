# Crypto Hourly Collector Spec

Updated: 2026-09-26
Timezone: Asia/Bangkok

## 目标

每小时生成可靠、轻量、可供 09:00 日报和 Mission 使用的增量素材。优先“持续成功”，不追求单轮穷尽全网。

## Start-of-run heartbeat

Before doing broad research, create a unique minimal run audit:

`crypto-daily/runs/YYYY-MM-DD/HHMMSS.md`

Initial status: `in_progress`.

This heartbeat is mandatory. If later research or a source fails, finalize the same audit as `partial_failure` / `failed`. A scheduler trigger with no audit is a missing run.

If create-file path collides, use a new second-level timestamp and retry once. If a state/file update requires SHA, fetch the latest SHA immediately before update and retry once on conflict.

## 每轮预算

最多保存 8 个 material candidates。超出部分按：
1. 安全/黑客；
2. BTC/ETH/SOL 与高流动性资产；
3. 重大监管/宏观；
4. 一级市场/TGE/ICO；
5. NFT/新生态；
排序截断。

## 强制扫描

- BTC / ETH / SOL 与主要衍生品状态；
- 24h/7d 异常资产；
- 交易所/官方/监管；
- 安全事件；
- X 英文高信号；
- Reddit；
- NFT / digital art；
- 跨链/跨平台价差线索；
- prediction markets；
- 主要链生态。

单个 source 不可用时继续其它 source。

## Research 文件

路径：
`crypto-daily/research/YYYY-MM-DD/HHMMSS.md`

要求：
- 只写 paraphrase；
- 不复制长段网页/X 原文；
- 不保存 exploit 操作步骤；
- URL 只保留必要的一手引用，不做 URL dump；
- 每候选最多约 120-180 字；
- 无 material update 时写极短 `no_material_update`。

## 写入降级

第一次 research create/update 被拦截时，立即降级为 compact schema：

```text
topic
why_it_matters
confirmed_facts
market_snapshot
source_names/domains
confidence
unresolved
```

不包含长引文、长 URL、恶意代码、利用步骤。

若 compact write 仍失败：
- run_status = partial_failure；
- finalize 已创建的 skeleton run audit，记录真实 connector/tool error；
- 不发用户通知；
- 下一轮独立继续。

## Run audit

每轮必须写：
`crypto-daily/runs/YYYY-MM-DD/HHMMSS.md`

至少记录：
run_time, automation_id, run_mode=hourly_research, run_status,
research_path, candidate_count, sources_ok, source_failures,
x_scanned, reddit_scanned, market_scanned, security_scanned,
github_research_write, github_audit_write, tool_errors。

## 禁止

- 本任务不发 Gmail。
- 本任务不生成正式 13 章日报。
- 本任务不做历史全量回填。
- 本任务不因 GitHub research 写失败而继续生成超长重试内容。
