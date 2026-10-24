# 2026-10-18 P4-B：D503 两笔真实 BUY gasUsed 闭合，E11B 未确认

仓库 PR #40，原冻结 23 EOA × 19 exact CA（437 格）不扩张。D503 与 E11B 均为原 23 以外的**原有已记录市场观察样本**，不是新的候选聪明钱。

## 本轮实际链上证据与计算

在 [7 次上限的精确预冻结](./bsc-meme-address-model-v1-p4b-dragon-three-real-buys-adjacent-cumulative-gas-precommit-2026-10-18.json) 提交后，使用既有 Alchemy BNB 主网免费只读接口，实际执行 6 次请求（3 笔原买单前序交易读取、2 笔完整前序 receipt、1 笔 E11B 原买单 receipt），零重试。新 [回读结果](./bsc-meme-address-model-v1-p4b-dragon-three-adjacent-actual-gas-readback-2026-10-18.json) 是追加文件，原买单和钱包原来源不修改。

目标交易的 `cumulativeGasUsed` 已存在旧冻结的 [D503 两买单工具截断记录](./bsc-meme-address-model-v1-p4b-dragon-d503-two-buy-gas-trace-free-tier-result-2026-10-18.json) 中，本轮读取**同一区块紧邻上一笔交易**完整 receipt 的累计 Gas。按共识交易顺序：

`目标实际 gasUsed = 目标 receipt cumulativeGasUsed − 紧邻前一笔 receipt cumulativeGasUsed`。

| 项目 | D503 第一笔 BUY | D503 第二笔 BUY |
|---|---:|---:|
| 历史区块 | 83,636,000 | 83,636,084 |
| 买单索引 → 前序索引 | 1 → 0 | 55 → 54 |
| 旧目标回执 `cumulativeGasUsed` | `0x4fa3f` | `0x1ac4653` |
| 前一笔完整回执 `cumulativeGasUsed` | `0x8b38` | `0x1a7d74c` |
| **真实买单 gasUsed** | **290,567** | **290,567** |
| 原签名交易实际 gasPrice | 3 gwei | 7 gwei |
| **真实买单 Gas 费** | **0.000871701 BNB** | **0.002033969 BNB** |
| 原交易 `tx.value` | 0.190 BNB | 0.220 BNB |
| 原钱包真实整块 BNB 余额支出 | 0.190871700999999996 | 0.222033968999999982 |
| 整块余额净支出减去 (tx.value + Gas 费) | **−4 wei** | **−18 wei** |

两次都通过前序交易 `ethGetTransactionByBlockNumberAndIndex` 验证紧邻索引、block、hash，且前序 receipt 完整 JSON 可解析。目标 BUY receipt 本身仍被工具截断，**不是完整原始回执归档**。GasUsed 是由已固定的两个链上累计字段和严格相邻索引**独立求差**，不是拿钱包余额差值倒推。链上 legacy type-0 买单的 `gasPrice` 从已归档原签名交易读取。

钱包买入区块余额差已包含 Gas，不能重复扣除。4 wei／18 wei 是**尚未归因的真实余额差异**，即使数量极小，也不能宣称完全没有其他资金流、退款或区块内其他交易。由此证明**两笔原 D503 BUY 的实际 Gas 费用**，不意味着已经完成其整个合约调用链的逐层现金流归因。

## 未确认的买单与策略边界

E11B 原成功 BUY 的 index=67，所需前序 index=66；其前序交易读取遭 8,098 字符工具截断，未可靠保存完整前序交易 hash，因此没有读取前序 receipt。E11B 原买单 receipt 亦被截断，仅能看到目标累计值 `0x8f7e66`，不足以求差。E11B 买入 gasUsed、手续费、退出、盈亏仍为 **UNRESOLVED**，继续保留于同批对照，不能为提高 D503 成功率而排除。

D503 两轮本人真实买入到本人真实卖出的链上时间分别约 9 秒／5 秒，先前真实选定钱包余额累计净变化约 +0.061218026868859435 BNB。这些是**后验实际交易者自身的交易与区块余额变化**；信号主人 DDAC 在 D503 买入之前 **200 个区块已经清仓**，因此这不是 DDAC 的可复制跟单获利，更不是固定 +1/+5/+15 分钟外部交易者净收益。

证据强度：`ADJACENT_RECEIPT_TOOL_PARSED_AND_TARGET_OLD_TOOL_VISIBLE_PREFIX_NOT_COMPLETE_TARGET_PROVIDER_WIRE`，前序回执完整、目标累计旧工具可见、未归档完整供应商网络传输层包。完整 [独立 SHA 固化差分重算](./bsc_meme_address_model_v1_p4b_dragon_adjacent_actual_buy_gas.py) 与 [13 项对抗测试](./test_bsc_meme_address_model_v1_p4b_dragon_adjacent_actual_buy_gas.py) 已纳入 Ubuntu/macOS 全量 CI，确保不能把 Gas 上限冒充实际 Gas、把小额残差变零，或假报 E11B 已退出。

**真正下一步**：在原冻结样本中寻找第三方**收到原钱包信号之后**的可证实买入（接收时间、足额本金、交易成功）、对应真实卖出和完整支付费用，建立时间条件与亏损/未知退出负对照。不可把这次解决的真实 Gas 缺口误报为 `PUBLIC_EXECUTABLE_U` 或 P5 已完成。保持 `P4-B=PARTIAL / PUBLIC_EXECUTABLE_U=UNRESOLVED / P5=BLOCKED / PRODUCTION=NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。
