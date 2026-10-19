# FRANK_G2_D1_D2_MAC_READONLY_ACCEPTANCE 证据包

- 被测固定 SHA：`3e8eb8bbd2e84762578fda09e03091cc47d8adb7`（PR #119；本包不含任何产品代码）
- 状态：`MAC_READONLY_ACCEPTANCE_PARTIAL`（结论见 PR #119 评论）
- 数据：生产 live-v1 只读副本，观察时间约 2026-10-20 01:05–01:30（本地时间）
- 截图已脱敏：仅含缩写地址，无本地绝对路径，无完整钱包地址或原始签名。

| 文件 | sha256 | 内容 |
|---|---|---|
| normal_d1_24h.png | d696eebc6a4b526f15d58ceb52b8c9ce9e298680937e23f1a8735364456b50a5 | 正常实例 D1 24 小时摘要与表格 |
| fault503_header_candidates.png | d9cb71820a22f8ada42e9f43bc1cf8340cc867d0dfed991e514933d9e18936f9 | 历史判断 503 故障实例：页头与候选区仍显示 |
| fault503_d2_holdings.png | 0d31a7ad5d37723384a495cf123c4bd70aa5f04685ee2ac13642dd81d9f8c17f | 503 故障实例：D2 观察池与 2026-10-11 非实时标注 |
| interact_after.png | d39987b383533070ed477944d74a329a774f3dd357c172a1cd01ae148cc71552 | 正常实例 D2 搜索后“已复制到剪贴板”提示 |

本包只含验收材料，不含代码，不修改生产数据，不合并、不部署。
