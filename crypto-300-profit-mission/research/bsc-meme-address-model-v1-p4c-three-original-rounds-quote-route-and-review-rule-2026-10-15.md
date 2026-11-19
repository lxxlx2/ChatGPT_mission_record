# BSC Meme 地址分析 V1 — P4-C 冻结三组交易的真实代币闭合与报价路径门禁

**时间：** 2026-10-15（Asia/Bangkok）。**分支：** `research/bsc-address-model-v1-20261013`，原 Draft PR #40。

**结论：** 已固定的 ADFF／龙虾、2ADF／牛来、A83B／牛来三组原始本人签名样本经独立链上事件验证 **3/3 代币买卖数量完全闭合**；但报价经路由的完整用户经济回款、费用/Gas、原始完整回执仍未全部闭合，因此 **新增已审计正收益 0、负收益 0**，不得修改先前的 23 钱包收益排名或将其用于跟单。P4-C 仍 PARTIAL；P5 / production NO_GO。

## 样本、交易及实际观察

源预冻结文件：`bsc-meme-address-model-v1-p4c-three-unclosed-router-event-precommit-2026-10-15.json`；全部保留原 7 个预选本人签名交易 hash、原始区块、钱包、exact CA（不是看结果后重选）。

| 原始样本 | 原始代币买卖数量 | 验证的报价流向 | 已有历史账户 BNB 区块净变动 | 经济分级 |
| --- | --- | --- | --- | --- |
| ADFF 龙虾 | 买入 = 卖出 `116550039851143133337499` 最小单位；残余 0 | 同笔卖出，真实 WBNB `206830246399802680` wei 从原流动性场所进入路由合约 `0x1de460f363af910f51726def188f9004276bf4bc` | **+0.004522437855804654 BNB** | 仅真实 token 库存闭合；WBNB→签名钱包原生币及费用尚不能逐项核销 |
| 2ADF 牛来 | 买入 = 卖出 `13211550674646819143983` 最小单位；其中 `132115506746468191439` 最小单位转入 token 合约 | 同笔卖出，原历史非原生报价代币 **Q3B** `0x205812cdbed920aff76c6580abd681a46d11efc7` 的 `111554339344126621` 最小单位从原场所进入路由合约 | **+0.031837686901930499 BNB** | Token 库存闭合，报价 Q3B 与 BNB 账户净值不可直接相加 |
| A83B 牛来 | 两笔买入合计 = 卖出 `94673211735825585728593` 最小单位；其中 `946732117358255857285` 转入 token 合约 | 同笔卖出，真实 Q3B `2264079415872901600` 最小单位向同一路由合约转出 | **−0.213598956812665039 BNB** | Token 库存闭合；两笔买单位于同一区块，BNB 账户余额只按一个独立区块计算 |

*这两笔转入牛来 token 合约的最小单位恰好约为原始卖出代币数量的 1%，但**不能仅从转账目的地就断言所有费用归属或兑换汇率**。真正到账钱包的币种、税费、Gas 和路由全链条必须另外验真。*

特别否定证据：A83B 买入区块 `116113193` 中，发现不属于选定的三笔 A83B 原始买卖交易的一笔**第三方** Q3B 转账：`0x79df9ac69ddd2a54d0a6dd5c8d2b07319bd2f45d41c1e4d1a1f2fd95485bfa19`。它已被精确原始 tx hash 过滤排除；不能把它当作 A83B 的现金流。四个唯一牛来区块的 WBNB *直接从原池子转出*过滤查询均无匹配，但这 **不代表** 多跳路由没有 WBNB 或 BNB 结算。

## Git 交付和验收证据

- 真实 raw ERC20：`bsc-meme-address-model-v1-p4c-three-unclosed-ADFF-transfer-probe-2026-10-15.json`、`bsc-meme-address-model-v1-p4c-three-unclosed-2ADF-token-events-2026-10-15.json`、`bsc-meme-address-model-v1-p4c-three-unclosed-A83B-token-events-2026-10-15.json`
- 报价原始链上：`bsc-meme-address-model-v1-p4c-three-unclosed-ADFF-WBNB-targeted-2026-10-15.json`、`bsc-meme-address-model-v1-p4c-three-unclosed-NIULAI-Q3B-outflow-2026-10-15.json`、`bsc-meme-address-model-v1-p4c-three-unclosed-NIULAI-WBNB-pool-2026-10-15.json`
- 标准化输出：`bsc-meme-address-model-v1-p4c-three-unclosed-owner-token-quote-gate-2026-10-15.json`，7 个原始 tx 3/3 token 完全闭合，两个 native block 正向、一个负向、**0 新经济回合提升**。
- 每份原始输入采用严格 Git blob SHA 清单；离线复算模型 `bsc_meme_address_model_v1_p4c_three_quote_gate.py`，对抗测试 `test_bsc_meme_address_model_v1_p4c_three_quote_gate.py`；包含强制独立 tx hash 排除、错误原始钱包、代币售出数量篡改、错误 Q3B 收款合约、约 1% token 合约转账不完整、无虚构跟单结论等。
- 本轮专项 [GitHub Actions CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38617741190) **SUCCESS**，现有 [BSC 主模型 CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38617741192) **SUCCESS**，原 [7 钱包核查 CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38617741291) 与 [8E6B 两正向 CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38617741244) 同 SHA 均通过。最终文档 HEAD 需单独检查。

## 规则更新与下一阶段主线

已新增 `bsc-meme-address-model-v1-development-rules-2026-10-15.md`，并将其置于主实施计划顶部：**需其他 AI Review 时，必须在用户当前回复提供固定 40 位 SHA、原 PR、来源、CI、只读范围、可复制的完整审核提示词；不能只称需要 Review**。这次跨样本新的资金口径及生产门禁可提交其他 AI **中途证据分级独立审核**；审核成功亦不等于整套 P5/G6 完成或部署通过。仍须收到另一 AI 真实审查结果，不能自我审批。

**Next:** 不再针对三个已经完成 token 库存但回款路径不支持免费精确 trace 的旧回合无限重试。下一批从历史 P2 的现有 50 个正负采样证据中预冻结新的 **多钱包、不同重大 CA、高等级结算样本**，批量审核实际签名人、完整入出报价、gas、税费、源资金，产生跨钱包可比正负经济回合，并反向验证观察者真实首可执行机会 U；然后才能进入 P5 out-of-sample 1/5/15 分钟延迟跟单。所有 `NO_GO/NO_MERGE/NO_DEPLOY` 不变，PR #40 未合并，未部署，无真钱交易与通知。
