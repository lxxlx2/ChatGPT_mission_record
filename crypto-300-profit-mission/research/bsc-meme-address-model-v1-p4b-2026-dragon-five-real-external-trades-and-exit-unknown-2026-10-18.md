# P4-B 龙虾：真实外部买家两轮快速退出与未退出对照（2026-10-18）

研究归属：Mission BSC Meme 地址分析建模，Draft PR #40。仍使用原 **23 EOA × 19 exact CA = 437** 冻结研究母数；本轮**不是新增聪明钱样本或 437 格策略回测**，而是审查之前就已锁定的 Dragon/龙虾 exact CA `0xeccbb861c0dda7efd964010085488b69317e4444` 里两名**原 23 钱包以外的实际独立市场买家**。

## 结果：D503 有真实快速买卖及正向历史钱包区块差，E11B 未证实退出

| 历史事实 | D503 第 1 轮 | D503 第 2 轮 | E11B 买入对照 |
|---|---:|---:|---|
| 实际原始签名买入区块 | 83,636,000 | 83,636,084 | 83,636,000 |
| 实际已保存的成功卖出区块 | 83,636,018 | 83,636,094 | **未确认** |
| 买卖区块头共识时间差 | **9 秒** | **5 秒** | 不适用 |
| 买入交易原生 `tx.value` | 0.190 BNB | 0.220 BNB | 0.012 BNB |
| 原买单 `gasPrice` | 3 gwei | 7 gwei | 0.057531543 gwei |
| 原钱包买入所在整块 BNB 余额流出 | 0.190871700999999996 | 0.222033968999999982 | 本轮未对账 |
| 原钱包授权及卖出所在整块 BNB 余额流入 | 0.215136579154473738 | 0.258987117714385675 | 未核实卖出 |
| **两个选定区块 EOA 净变化** | **+0.024264878154473742 BNB** | **+0.036953148714385693 BNB** | **UNRESOLVED** |
| 历史指定区块实际 ERC-20 库存 | 买后非零／卖后零 | 买后非零／卖后零 | 在块 83,636,127 **仍非零** |

D503 两轮共四个指定钱包区块 BNB 余额净增加 **+0.061218026868859435 BNB**；这是原钱包的**选定整块 BNB 余额差额**，非源 DDAC 的跟单利润，也未保证每个区块内所有原生收支均归因于这几笔已选交易。原 D503 本人两轮成功买单、代币到帐、完整卖币且余额归零均有独立旧签名和 `balanceOf` 历史归档；因此证明该市场确实存在之后第三方真实买入再卖出的样本。**但这不代表任何外部观察者能捕捉这 5–9 秒窗口。**

E11B 在与 D503 第一笔买单相同的块 83,636,000，已成功本人签名买入；原选定时间窗内至块 **83,636,127** 的其本人龙虾持币仍为 **347546637309143000000000 raw**。没有在冻结范围内完整证明 E11B 后来卖出或实际损益，必须保留 **EXIT_UNKNOWN**，不能为提高假设胜率将其当亏损排除或误作盈利。

**因果性反例：** 源 DDAC 的原龙虾买入块 83,635,776、完整卖出块 83,635,800，真实合约 `balanceOf(DDAC)` 在后续 D503 买入 83,636,000 仍是零。D503 是 **DDAC 已清仓后 200 块**才入场，既无接到 DDAC 提醒的记录，也不能把 D503 之后的收益归功于跟随 DDAC。E11B 与 D503 同块买入也不说明 E11B 模仿 D503。

## 本轮新获取的实际证据与成本事实

最初依据 [五笔独立浏览器核验预冻结](./bsc-meme-address-model-v1-p4b-dragon-five-actual-external-tx-independent-fee-precommit-2026-10-18.json) 要求使用 Blockscout 免费接口核对 Gas；该插件在已有 session 上明示必须配置 **Blockscout PRO API Key**，因此没有进一步重试、升级或购买服务。[访问拒绝原始工作结果](./bsc-meme-address-model-v1-p4b-dragon-five-external-blockscout-public-denied-2026-10-18.json) 独立归档；这不是交易失败或 Gas 为零。

随后明确新建 [同五笔固定交易 Alchemy 免费方案预冻结](./bsc-meme-address-model-v1-p4b-dragon-five-external-signer-original-tx-alchemy-free-precommit-2026-10-18.json)，**一个钱包／交易均未更换**。通过免费只读 BNB 主网 `eth_getTransactionByHash` 恰好五次，**5/5 完整解析，零重试**；原始签名 sender、哈希、nonce、真实 `tx.value`、`gasPrice`、`gas`、blockNumber、blockTimestamp 与以往旧文件逐笔匹配；工具解析字段见 [真实五笔交易新来源](./bsc-meme-address-model-v1-p4b-dragon-five-external-signer-original-tx-alchemy-readback-2026-10-18.json)。本轮 Alchemy 工具回读完整交易字段，但不声称保存了供应商传输层逐字节原始包。

**Gas 口径必须严格区分：**

- `eth_getTransactionByHash.gas` 是交易**设定的 Gas 上限**，不是实际 `gasUsed`。两笔 D503 买单的 `gas` 都是 600,000，实际消耗的 Gas 在此前完整 receipt 被工具截断后**仍未由独立免费 receipt 证实**，不得用上限或钱包差额伪造单笔实际 Gas。
- D503 两轮**授权与卖出**的原始旧完整 receipt 各自确认 46,327 + 211,830 Gas，价格 2 gwei，所以两笔操作的**该两笔已核实 Gas**每轮 **0.000516314 BNB**；但不代表同块没有其他 BNB 流，也不能在前述本来已经包含交易 Gas 的钱包区块净变化上重复扣费。
- D503 第 1、2 笔买单原 `tx.value` 为 0.190／0.220 BNB，买入块 EOA 整块支出分别高于原 `tx.value`；多出来的部分可能包括买单 Gas 和其他原生转账，**不能单靠差额认定交易税或逐笔实际 Gas**。E11B 买入后还持有龙虾，缺少可核实卖出和资金回款。

[固定来源重算脚本](./bsc_meme_address_model_v1_p4b_dragon_external_five_true_txs.py) 同时锁定旧实际七笔 signed 交易、四个历史 BNB 余额、十二个历史代币余额、DDAC 提前清仓来源及新五笔免费交易字段；校验三类实际成果：D503 两轮自己买卖、同区块 E11B 的买入但未核实退出、老 DDAC 早已退出而且没有跟单因果性。[13 个对抗测试](./test_bsc_meme_address_model_v1_p4b_dragon_external_five_true_txs.py) 防止更换钱包/币/交易、冒充买单 receipt Gas、抹掉 E11B 仍持有的代币、修改 selected BNB 净额或把 Blockscout access denied 说成交易 Gas 已确认。

## 对推荐模型的实际含义

1. 不能因为某个后续买家在 **5–9 秒内**实际获利，就将这轮机会自动标记为普通用户能跟单；需先取得可观察信号推送时间、下单延迟和成交资金证据。
2. **提前清仓的原信号必须过期**，后续有人赚到钱不意味着早期原信号尚可交易；这一反例有历史真实链上余额证实。
3. 不能按“只统计最后确实卖出赚钱的人”计算聪明钱胜率。E11B 的实际买单和未知退出必须留在相同固定样本的分母或以可解释的 censored/UNKNOWN 方式呈现。
4. 若试图把未来模型发布为用户可执行的信号，下一真正里程碑是**外部信号可观察时刻＋固定延迟成交价／资金成本／Token 到账与实际退出**的同一交易路径闭合，而不是继续重复测试这些已有原主交易。

状态保持 `P4-B=PARTIAL / PUBLIC_EXECUTABLE_U=UNRESOLVED / P5=BLOCKED / PRODUCTION=NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。未买付费 Key，未合并、未部署、未发邮件、未交易。
