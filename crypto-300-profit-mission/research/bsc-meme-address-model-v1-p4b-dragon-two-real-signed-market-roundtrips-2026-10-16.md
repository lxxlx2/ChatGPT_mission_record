# BSC Meme P4-B：DDAC 龙虾买入后的两名真实市场买家，已找到同钱包两次原签名买卖（仅研究）

**日期：2026-10-16（Asia/Bangkok）**。原 Mission [Draft PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40)；固定需求 `bsc-meme-address-model-v1-requirements-2026-10-13.md` 和开发规则不变。**只读 BNB Mainnet / 不合并、不部署、不邮件、不交易。** 本批按先冻结再查出场的顺序执行，不能把原钱包经济正方向升级为外部观察者跟单盈利。

## 1. 先冻结的母集和真实扫描

在获得新的退出交易之前，先提交 [固定两名买家及窗口的 precommit](./bsc-meme-address-model-v1-p4b-dragon-postowner-signed-roundtrip-precommit-2026-10-16.json)：从此前已固定的区块 **83636000** 两个龙虾 exact CA 的 Four.meme V2 `TokenPurchase` / `Transfer` 中，预选两名**原始实际签名买方**：

| 固定买家 | 区块 83636000 原买入哈希 | 冻结 23 EOA 内？ | 查询范围 |
|---|---|---|---|
| D503 `0xd503f69b37efbfe510e37f46a4ca34e0adb1a7aa` | `0xd099d33a83c217e47f21b618483ae48de6018fb7fd26d093924f2eb25d219118` | **否** | 83636001–83636127 |
| E11B `0xe11b917d591db3bf40ecb5bf7ea4ea5af503460c` | `0xc0262a91f9e2036a5700f88753aec82496104410b8d8a02610f33c8a2d5a6c7a` | **否** | 相同 |

目标 CA `0xeccbb861c0dda7efd964010085488b69317e4444`，Four.meme V2 TokenManager2 `0x5c952063c7fc8610ffdb798152d69f0b9550762b`。原信号钱包 DDAC `0xddac928a240bdace3994c2cc0783d4e29a002127` 在 **83635776** 实际签名买入，08:48:02.150Z；本批初始两名买家区块 **83636000 = 08:49:42.950Z**，二者相距 **100.8 秒**（是区块头时间差，**不是公开节点消息可见性或下单延迟**）。

Alchemy 免费层 `eth_getLogs` 限单请求至最多 10 个块，因此针对**两名全部预选买家**，分别拆成 **13 个无缝覆盖区间**，一共 **26 个原始 ERC20 `Transfer(from=buyer,to=TokenManager2)` 查询**，全部成功、无截断、无省略中间区间：
- [D503 13 个原始窗口](./bsc-meme-address-model-v1-p4b-dragon-d503-exhaustive-curve-sell-scan-2026-10-16.json)：**两条出向**，分别在 83636018 和 83636094。
- [E11B 13 个原始窗口](./bsc-meme-address-model-v1-p4b-dragon-e11b-exhaustive-curve-sell-scan-2026-10-16.json)：**零条同一曲线 manager 方向出向**。**不表示其不可能通过其它路由/DEX 卖出，更不能记为亏损。**

两者均在原 V21 23 钱包全集之外。它们是**已暴露的事后市场参与者观察案例**，不属于新冻结的高盈利钱包发现集合，也不是 untouched P5 holdout。

## 2. D503：两套本人买入→授权→卖出原交易均成功

[七笔原始发送人交易、回执与相关事件](./bsc-meme-address-model-v1-p4b-dragon-postowner-original-seven-txs-2026-10-16.json) 保存 6 笔 D503 交易与一笔 E11B 买入。D503 原交易 `tx.from` 全是同一个 EOA，所有可读原回执 `status=0x1`；两次 `Approval(spender=TokenManager2,amount=持币数量)` 后各发生 `TokenSale.account=D503`，对应 Dragon ERC20 全额 `Transfer(D503→TokenManager2)` 与两条完整卖出成功回执。两次买入原回执因长度截断，只提取并标注可读 status/event；**不得假装取得完整 gasUsed**。

| 项目 | 第一次（D503） | 第二次（D503） |
|---|---|---|
| 实际原买入 tx | `0xd099d33a83c217e47f21b618483ae48de6018fb7fd26d093924f2eb25d219118` | `0xbc1622bb9a1850b5966f7c056d0344e586c3ffcf7b882df84cb07673bd13bfb5` |
| 买入时间（块末） | 08:49:42.950Z，83636000 | 08:50:20.750Z，83636084 |
| 签名授权 tx | `0x0b6a3d872ef79a5b6b6048151340e399935d3167bcc3fc2f2ca26ee3574a83b4` | `0x8b7765c0f34c1f2cb7b41798ca5e5b50c772d2ad7eafd4bbbb1de1a66e33fae0` |
| 实际卖出 tx | `0x854ce4c5edc725bf9d763c043e29e0d8ef8a9ab89a3c39bdf7fba31dda98416d` | `0x25122e07f529fc935856f99cc948f442587ac09d1e339a859eb86537e93eca0a` |
| 卖出时间（块末） | 08:49:51.050Z，83636018 | 08:50:25.250Z，83636094 |
| 原始 Dragon raw 量 | `5033644503996605000000000` | `3119477321356746000000000` |
| 发出买入 BNB `tx.value` | 0.190000000000000000 | 0.220000000000000000 |
| 原 `TokenSale.cost`（BNB） | 0.220053972606605854 | 0.264799420116720075 |
| 原 `TokenSale.fee`（BNB） | 0.002200539726066058 | 0.002647994201167200 |

[按历史区块逐块读取 ERC20 balanceOf](./bsc-meme-address-model-v1-p4b-dragon-two-buyers-historic-token-inventory-2026-10-16.json)：D503 的区块末代币数量依次 **0 → 第一次买入数量 → 0 → 第二次买入数量 → 0**。E11B 在 83636000 收到 `347546637309143000000000` raw，直至本次退出扫描边界 **83636127** 仍持有同额。没有用 ERC20 数量替代签名授权或结算证据。

## 3. 四个交易区块的原生 BNB 钱包余额和费用

[历史 EOA BNB 原始余额及差额](./bsc-meme-address-model-v1-p4b-dragon-two-buyers-historic-native-balances-2026-10-16.json)：

| D503 EOA 区块余额边界 | 本区块 BNB 余额变化（wei） | 类型 |
|---|---:|---|
| 83635999 → 83636000 | −190871700999999996 | 第一次原买入块 |
| 83636017 → 83636018 | +215136579154473738 | 第一次 Approval + TokenSale 块 |
| 83636083 → 83636084 | −222033968999999982 | 第二次原买入块 |
| 83636093 → 83636094 | +258987117714385675 | 第二次 Approval + TokenSale 块 |

上述四个**已选区块**的 EOA 原生余额差额相加为 **`+61218026868859435 wei`，即 +0.061218026868859435 BNB**；第一次买卖相关区块合计 **`+24264878154473742 wei`**，第二次 **`+36953148714385693 wei`**。

对卖出块做了进一步**精确整数对账**，而不是拿历史 spot 报价推算：

`钱包卖出块 BNB delta = TokenSale.cost − 2 × TokenSale.fee − 原签名 Approval 实际 Gas − 原签名卖出实际 Gas`

两次卖出块都**逐 wei 完全相等**。每一次同块授权 Gas 为 `46327 × 2 gwei = 92654000000000 wei`，卖出 Gas 为 `211830 × 2 gwei = 423660000000000 wei`。这一等式真实闭合了**选定区块的原钱包原生余额净流入及两笔同块签名交易 Gas**，但 `TokenSale.fee` 需要乘 2 才吻合实际钱包数据，**不得在缺乏合约内部跟踪时杜撰第二项 fee 的法律/业务含义或受益人**。

买入 `tx.value − 原 TokenPurchase.cost − 原 TokenPurchase.fee` 分别为 **`1900000000000004 wei`** 和 **`2200000000000018 wei`**，费/退款归属仍未核实。对应买入块 EOA 余额变化与 `tx.value` 之差接近一次 Gas，但精确 Gas 不能仅凭截断回执证明；与估计每次 `290567 gas` 的差额分别 **4 wei / 18 wei**，不在此归为已确认退款。

**证据等级：** `SIGNED_ACTUAL_OWNER_TOKEN_ROUNDTRIPS_CONFIRMED`；`SELECTED_NATIVE_WALLET_BLOCK_DELTA_POSITIVE`；但由于买入收据 Gas 不完整、无免费 internal trace、未全量排除任意内部原生转账，**`FULL_TRANSACTION_ATTRIBUTABLE_NATIVE_REALIZED_PNL = UNRESOLVED`**。不据此声称原钱包的全部历史盈利、跟单 ROI 或税后净收益。

## 4. 研究结论与下一步边界

1. 对**事后确定的 DDAC 龙虾原始签名买入**，这批首次找到了其他钱包 **D503** 实际在它之后买到代币、授权并两次卖出完毕的链上成功交易。这比 `eth_call` 数学报价和三名不同地址只卖出强。**但没有证明 D503 当时看到 DDAC 信号、模仿 DDAC、其真实订单最早公开可知时间或第三方可以在相同时间成交**。两个买入时刻是 DDAC 买入**约 100.8 秒与 138.6 秒后的区块头时间**，不能当作固定 1/5/15 分钟跟单回测。
2. 严格保留 E11B 未退出对照与 13/13 无截断空查询；`ZERO_MANAGER_EXIT` 不是 `ZERO_SELL_ANYWHERE`、亏损或无交易。
3. 不扩张初始冻结的 23×19 样本；D503 和 E11B 只做**外部已暴露市场案例**，不计入 23 钱包优质地址排行，不适用 P5 untouched。
4. 下一研究批应转回**跨多个重大 CA、跨冻结钱包的原始签名经济正负对照**，并单独冻结可得的 2026 公开机会 U 起点与 1/5/15 分钟时间，不在这两条已暴露的 Dragon 钱包上调利润阈值或迭代择时。

**阶段标记：** `P4-B=PARTIAL`，`PUBLIC_EXECUTABLE_U=UNRESOLVED`，`P4-C=PARTIAL`，`P5=BLOCKED`，`NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。新增经济门禁代码和来源必须交另一 AI 针对当轮**固定 SHA**独立审核，不能继承此前 macOS CI 修复的窄范围 `APPROVE`。
