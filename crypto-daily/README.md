# Crypto Daily

一个现有 `Crypto 每日情报` automation 同时负责小时素材、09:00 正式日报和缺报恢复。

## 文件

- `COLLECTOR_SPEC.md`：普通小时轻量采集
- `REPORT_SPEC.md`：正式 13 章日报
- `DELIVERY_RUNBOOK.md`：09:00 / 10:00 / 11:00 发布与恢复
- `research/`：小时素材
- `reports/daily/`：正式日报
- `runs/`：每轮 audit

## 普通小时

每小时：
- 核心 BTC / ETH / SOL 与 security scan
- bulk market 异常扫描
- 一个 rotating discovery shard

3 小时覆盖：
- X / Reddit / NFT
- ecosystem / TGE / ICO / prediction
- whale / derivatives / cross-chain / macro / deeper security

这样降低单轮工作量，同时保持滚动覆盖。

## 09:00

Delivery first：

1. skeleton audit
2. 检查当天 Gmail + GitHub
3. 若缺报，使用过去 24h research + 少量 fresh verification
4. 生成并 QA 13 章
5. Gmail first + readback
6. GitHub archive + readback
7. 交付完成后才做可选的新增研究

## 10:00 / 11:00

Recovery first。

如果当天正式日报缺一侧，优先修复。已经完整送达时才进入普通小时采集。

Gmail 已经成功后，即使 GitHub 后续失败，也不能重复发送正式日报。

## 审计

每轮第一项持久化动作先写 skeleton audit，最后 finalize。

正常 `no_material_update` 是健康结果。
